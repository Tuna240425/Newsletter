import pandas as pd
import os
import streamlit as st
from utils import validate_email

def get_email_column_name(df):
    """DataFrame에서 이메일 컬럼명을 찾는 함수"""
    if df.empty:
        return None
    
    # 가능한 이메일 컬럼명들
    possible_email_columns = ['이메일', 'email', 'Email', 'EMAIL', '메일', 'mail', 'Mail']
    
    for col in possible_email_columns:
        if col in df.columns:
            return col
    
    # 이메일 형식이 포함된 컬럼 찾기
    for col in df.columns:
        if df[col].dtype == 'object':  # 문자열 컬럼만 체크
            sample_values = df[col].dropna().head(5)
            for value in sample_values:
                if isinstance(value, str) and '@' in value and '.' in value:
                    return col
    
    return None

def get_name_column_name(df):
    """DataFrame에서 이름 컬럼명을 찾는 함수"""
    if df.empty:
        return None
    
    # 가능한 이름 컬럼명들
    possible_name_columns = ['이름', 'name', 'Name', 'NAME', '성명', '이름성명', '수신자']
    
    for col in possible_name_columns:
        if col in df.columns:
            return col
    
    # 첫 번째 컬럼을 이름으로 가정
    return df.columns[0] if len(df.columns) > 0 else None

def normalize_address_book(df):
    """주소록 DataFrame의 컬럼명을 표준화하는 함수"""
    if df.empty:
        return pd.DataFrame(columns=['이름', '이메일'])
    
    email_col = get_email_column_name(df)
    name_col = get_name_column_name(df)
    
    if email_col is None:
        st.error("이메일 컬럼을 찾을 수 없습니다. '@' 기호가 포함된 이메일 주소가 있는지 확인해주세요.")
        return pd.DataFrame(columns=['이름', '이메일'])
    
    if name_col is None:
        st.warning("이름 컬럼을 찾을 수 없어 첫 번째 컬럼을 이름으로 사용합니다.")
        name_col = df.columns[0]
    
    # 새로운 DataFrame 생성
    normalized_df = pd.DataFrame()
    normalized_df['이름'] = df[name_col]
    normalized_df['이메일'] = df[email_col]
    
    # 빈 이메일 제거
    normalized_df = normalized_df[normalized_df['이메일'].notna()]
    normalized_df = normalized_df[normalized_df['이메일'].str.strip() != '']
    
    return normalized_df

def save_address_book(address_book_df):
    """주소록을 파일로 저장"""
    if not address_book_df.empty:
        try:
            filename = "address_book_auto_save.csv"
            address_book_df.to_csv(filename, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            st.error(f"주소록 저장 실패: {e}")
            return False
    return False

def load_address_book():
    """저장된 주소록 파일 불러오기 (개선된 버전)"""
    try:
        filename = "address_book_auto_save.csv"
        if os.path.exists(filename):
            df = pd.read_csv(filename, encoding='utf-8-sig')
            # 주소록 정규화
            df = normalize_address_book(df)
            return df
    except Exception as e:
        st.error(f"주소록 불러오기 실패: {e}")
    return pd.DataFrame(columns=['이름', '이메일'])

def validate_address_book(df):
    """주소록 유효성 검사"""
    if df.empty:
        return False, "주소록이 비어있습니다."
    
    email_col = get_email_column_name(df)
    if email_col is None:
        return False, "이메일 컬럼을 찾을 수 없습니다."
    
    # 유효한 이메일 개수 확인
    valid_emails = 0
    invalid_emails = []
    
    for idx, email in df[email_col].items():
        if pd.notna(email) and str(email).strip():
            if validate_email(str(email).strip()):
                valid_emails += 1
            else:
                invalid_emails.append(f"행 {idx+1}: {email}")
    
    if valid_emails == 0:
        return False, "유효한 이메일 주소가 없습니다."
    
    if invalid_emails:
        warning_msg = f"유효한 이메일: {valid_emails}개\n잘못된 이메일: {len(invalid_emails)}개"
        if len(invalid_emails) <= 5:
            warning_msg += "\n잘못된 이메일:\n" + "\n".join(invalid_emails)
        return True, warning_msg
    
    return True, f"모든 이메일이 유효합니다. (총 {valid_emails}개)"

def clean_address_book(df):
    """주소록 정리 (중복 제거, 빈 값 제거 등)"""
    if df.empty:
        return df
    
    # 빈 값 제거
    df = df.dropna(subset=['이메일'])
    df = df[df['이메일'].str.strip() != '']
    
    # 이메일 중복 제거 (소문자로 변환하여 비교)
    df['이메일_lower'] = df['이메일'].str.lower().str.strip()
    df = df.drop_duplicates(subset=['이메일_lower'], keep='first')
    df = df.drop(columns=['이메일_lower'])
    
    # 이름이 비어있는 경우 이메일로 대체
    df.loc[df['이름'].isna() | (df['이름'].str.strip() == ''), '이름'] = df['이메일']
    
    return df.reset_index(drop=True)

def add_contact(address_book_df, name, email):
    """연락처 추가"""
    if not name or not email:
        return address_book_df, "이름과 이메일을 모두 입력해주세요."
    
    if not validate_email(email):
        return address_book_df, "올바른 이메일 형식이 아닙니다."
    
    # 중복 확인
    if not address_book_df.empty:
        existing_emails = address_book_df['이메일'].str.lower().str.strip()
        if email.lower().strip() in existing_emails.values:
            return address_book_df, "이미 존재하는 이메일 주소입니다."
    
    # 새 연락처 추가
    new_contact = pd.DataFrame({'이름': [name.strip()], '이메일': [email.strip()]})
    
    if address_book_df.empty:
        result_df = new_contact
    else:
        result_df = pd.concat([address_book_df, new_contact], ignore_index=True)
    
    return result_df, "연락처가 성공적으로 추가되었습니다."

def remove_contact(address_book_df, index):
    """연락처 제거"""
    if address_book_df.empty or index < 0 or index >= len(address_book_df):
        return address_book_df, "잘못된 인덱스입니다."
    
    result_df = address_book_df.drop(index=index).reset_index(drop=True)
    return result_df, "연락처가 제거되었습니다."

def export_address_book(address_book_df, format='csv'):
    """주소록 내보내기"""
    if address_book_df.empty:
        return None, "내보낼 주소록이 없습니다."
    
    try:
        if format.lower() == 'csv':
            csv_data = address_book_df.to_csv(index=False, encoding='utf-8-sig')
            return csv_data, "CSV 형식으로 내보내기 완료"
        else:
            return None, "지원하지 않는 형식입니다."
    except Exception as e:
        return None, f"내보내기 실패: {e}"

def import_address_book(uploaded_file):
    """주소록 가져오기"""
    try:
        # 파일 형식에 따른 읽기
        if uploaded_file.name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(uploaded_file, encoding='cp949')
                except:
                    df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        else:
            return None, "CSV 파일만 지원됩니다."
        
        if df.empty:
            return None, "빈 파일입니다."
        
        # 주소록 정규화
        normalized_df = normalize_address_book(df)
        
        if normalized_df.empty:
            return None, "유효한 데이터가 없습니다. 이메일 컬럼을 확인해주세요."
        
        # 정리
        cleaned_df = clean_address_book(normalized_df)
        
        return cleaned_df, f"주소록 가져오기 완료 (총 {len(cleaned_df)}개 연락처)"
        
    except Exception as e:
        return None, f"파일 읽기 실패: {e}"