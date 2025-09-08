import requests
import xml.etree.ElementTree as ET
import re
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import streamlit as st
from config import COMPANY_CONFIG

def _extract_google_link_improved(link: str) -> str:
    """개선된 Google News 링크 추출 (에러 처리 강화)"""
    try:
        # Google News 리다이렉트가 아닌 경우 그대로 반환
        if "news.google.com" not in link:
            return link
            
        p = urlparse(link)
        if "news.google.com" in p.netloc:
            qs = parse_qs(p.query)
            if "url" in qs and qs["url"]:
                decoded_url = qs["url"][0]
                # URL 유효성 검사
                try:
                    parsed_decoded = urlparse(decoded_url)
                    if parsed_decoded.scheme and parsed_decoded.netloc:
                        return decoded_url
                except:
                    pass
        
        # 추출 실패시 원본 반환 (차단되더라도 일단 포함)
        return link
    except Exception as e:
        print(f"링크 추출 오류: {e}")
        return link

def parse_rss_date(date_str):
    """RSS pubDate를 파싱해서 YYYY.MM.DD 형식으로 변환"""
    if not date_str:
        return datetime.now().strftime('%Y.%m.%d')
    
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y.%m.%d')
    except:
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y.%m.%d')
        except:
            return datetime.now().strftime('%Y.%m.%d')

def fetch_naver_rss(url: str, timeout: float = 10.0):
    """네이버 뉴스 RSS 수집"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        r.encoding = "utf-8"
        root = ET.fromstring(r.text)
        items = []
        
        for it in root.findall(".//item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            pub_date = (it.findtext("pubDate") or "").strip()
            
            if not title or not link:
                continue
                
            # 제목에서 불필요한 태그 제거
            title = re.sub(r'<[^>]+>', '', title)
            title = re.sub(r'\[.*?\]', '', title).strip()
            
            formatted_date = parse_rss_date(pub_date)
            
            items.append({
                "title": title,
                "url": link,
                "date": formatted_date,
                "source": "Naver",
                "raw_date": pub_date
            })
        return items
    except Exception as e:
        return {"error": f"네이버 RSS 수집 실패: {e}"}

def fetch_daum_rss(url: str, timeout: float = 10.0):
    """다음 뉴스 RSS 수집"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        r.encoding = "utf-8"
        root = ET.fromstring(r.text)
        items = []
        
        for it in root.findall(".//item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            pub_date = (it.findtext("pubDate") or "").strip()
            
            if not title or not link:
                continue
                
            # 제목 정리
            title = re.sub(r'<[^>]+>', '', title)
            title = re.sub(r'\[.*?\]', '', title).strip()
            
            formatted_date = parse_rss_date(pub_date)
            
            items.append({
                "title": title,
                "url": link,
                "date": formatted_date,
                "source": "Daum",
                "raw_date": pub_date
            })
        return items
    except Exception as e:
        return {"error": f"다음 RSS 수집 실패: {e}"}

def fetch_google_rss(url: str, timeout: float = 10.0):
    """Google News RSS 수집"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        r.encoding = "utf-8"
        root = ET.fromstring(r.text)
        items = []
        
        for it in root.findall(".//item"):
            title = (it.findtext("title") or "").strip()
            link = _extract_google_link_improved((it.findtext("link") or "").strip())
            pub_date = (it.findtext("pubDate") or "").strip()
            
            if not title or not link:
                continue
                
            formatted_date = parse_rss_date(pub_date)
            
            items.append({
                "title": title,
                "url": link,
                "date": formatted_date,
                "source": "Google",
                "raw_date": pub_date
            })
        return items
    except Exception as e:
        return {"error": f"Google RSS 수집 실패: {e}"}

def fetch_mixed_rss(url: str, timeout: float = 10.0):
    """RSS 소스에 따라 적절한 수집 함수 선택"""
    try:
        if "naver.com" in url:
            return fetch_naver_rss(url, timeout)
        elif "daum.net" in url:
            return fetch_daum_rss(url, timeout)
        elif "google.com" in url:
            return fetch_google_rss(url, timeout)
        else:
            # 기타 RSS는 기본 방식 사용
            return fetch_google_rss(url, timeout)
    except Exception as e:
        return {"error": f"RSS 수집 실패: {e}"}

def create_news_cache_key(sources):
    """뉴스 소스 목록을 기반으로 캐시 키 생성"""
    sources_str = '|'.join(sorted(sources))
    return hashlib.md5(sources_str.encode()).hexdigest()

def get_sample_news():
    """샘플 법률 뉴스 데이터 생성"""
    sample_news = [
        {
            'title': '개인정보보호법 개정안 국회 통과',
            'url': 'https://news.example.com/law1',
            'date': datetime.now().strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '새로운 상속세 면제 한도 확대',
            'url': 'https://news.example.com/law2', 
            'date': (datetime.now() - timedelta(days=1)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '부동산 계약 관련 법률 개정 사항',
            'url': 'https://news.example.com/law3',
            'date': (datetime.now() - timedelta(days=2)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '근로기준법 개정으로 인한 기업 대응 방안',
            'url': 'https://news.example.com/law4',
            'date': (datetime.now() - timedelta(days=3)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '디지털세법 시행령 발표',
            'url': 'https://news.example.com/law5',
            'date': (datetime.now() - timedelta(days=4)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        }
    ]
    return sample_news

def collect_latest_news(limit: int = 5, fallback_on_fail: bool = True, force_refresh: bool = False):
    """개선된 뉴스 수집 함수 (베트남 뉴스 필터링 포함)"""
    sources = st.session_state.newsletter_data.get('auto_news_sources') or COMPANY_CONFIG['default_news_sources']
    
    # 캐시 확인
    cache_key = create_news_cache_key(sources)
    current_time = datetime.now()
    
    if not force_refresh and 'news_cache' in st.session_state:
        cache_data = st.session_state.news_cache
        if (cache_data.get('key') == cache_key and 
            cache_data.get('timestamp') and 
            (current_time - cache_data['timestamp']).total_seconds() < 1800):
            st.info("최근에 수집한 뉴스를 사용합니다. (강제 새로고침하려면 '강제 새로고침' 버튼을 사용하세요)")
            return cache_data['news']
    
    all_items = []
    titles_seen = set()
    urls_seen = set()
    errors = []
    successful_sources = 0

    # 베트남/외국 관련 키워드 (제외할 키워드들)
    exclude_keywords = [
        '베트남', 'vietnam', '하노이', '호치민', 
        '중국', 'china', '일본', 'japan',
        '태국', 'thailand', '필리핀', 'philippines',
        '말레이시아', 'malaysia', '싱가포르', 'singapore',
        '인도네시아', 'indonesia', '라오스', 'laos',
        '캄보디아', 'cambodia', '미얀마', 'myanmar'
    ]

    for i, src in enumerate(sources):
        try:
            print(f"소스 {i+1} 처리 중: {src}")
            res = fetch_mixed_rss(src, timeout=8.0)
            
            if isinstance(res, dict) and "error" in res:
                errors.append(f"소스 {i+1}: {res['error']}")
                continue
                
            successful_sources += 1
            valid_items = 0
            
            for item in res:
                # 제목과 URL 정리 및 검증
                title_clean = re.sub(r'\s+', ' ', item["title"].strip())
                url_clean = item["url"].strip()
                
                # 베트남/외국 뉴스 필터링 (여기서 직접 처리)
                title_lower = title_clean.lower()
                
                # 제외 키워드가 포함된 뉴스는 건너뛰기
                if any(keyword in title_lower for keyword in exclude_keywords):
                    print(f"외국 뉴스 필터링: {title_clean}")
                    continue
                
                # 중복 검사
                if title_lower in titles_seen or url_clean in urls_seen:
                    continue
                
                # 최소 품질 검사
                if len(title_clean) < 5 or not url_clean.startswith('http'):
                    continue
                
                # 차단된 Google News 링크 필터링
                if "news.google.com" in url_clean and "/articles/" not in url_clean:
                    continue
                    
                titles_seen.add(title_lower)
                urls_seen.add(url_clean)
                all_items.append({
                    **item,
                    "title": title_clean
                })
                valid_items += 1
                
                if len(all_items) >= limit * 3:
                    break
            
            print(f"소스 {i+1}에서 {valid_items}개 수집 완료")
                    
        except Exception as e:
            errors.append(f"소스 {i+1} 처리 중 오류: {str(e)}")
            continue
            
        if len(all_items) >= limit * 2:
            break

    # 날짜순 정렬
    try:
        all_items.sort(key=lambda x: datetime.strptime(x['date'], '%Y.%m.%d'), reverse=True)
    except:
        pass

    # 결과가 부족하면 샘플로 보충
    if len(all_items) < limit and fallback_on_fail:
        if successful_sources == 0:
            st.warning("모든 뉴스 소스에서 데이터를 가져오는데 실패했습니다. 샘플 뉴스를 사용합니다.")
            return get_sample_news()[:limit]
        elif len(all_items) < limit:
            sample = get_sample_news()
            need = limit - len(all_items)
            for item in sample[:need]:
                if item["title"].lower() not in titles_seen:
                    all_items.append(item)

    final_news = all_items[:limit]
    
    # 캐시 저장
    st.session_state.news_cache = {
        'key': cache_key,
        'timestamp': current_time,
        'news': final_news
    }

    if errors:
        st.info(f"일부 소스에서 문제가 발생했습니다 (총 {successful_sources}개 소스 성공):\n- " + "\n- ".join(errors[:3]))

    return final_news