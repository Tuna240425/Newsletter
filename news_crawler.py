#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
뉴스 수집 모듈
네이버, 다음 등에서 법률/사회 관련 뉴스를 자동 수집
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import time
import random
import re
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, parse_qs, quote



NAVER_RSS = {
    "society": "https://news.naver.com/rss/section/102.xml",
    "economy": "https://news.naver.com/rss/section/101.xml",
    "culture": "https://news.naver.com/rss/section/103.xml",
}

DAUM_RSS = {
    "society": "https://news.daum.net/rss/society",
    "economy": "https://news.daum.net/rss/economic",
    "culture": "https://news.daum.net/rss/culture",
}

GOOGLE_RSS_QUERIES = {
    "society": [
        "법원 OR 판결 OR 소송",
        "노동법 OR 근로기준법",
    ],
    "economy": [
        "공정거래법 OR 공정위",
        "개인정보보호법 OR 전자상거래법",
    ],
    "culture": [
        "저작권법 OR 명예훼손",
        "청소년보호법 OR 정보통신망법",
    ],
}

class NewsCollector:
    # ... (기존 코드 유지)

    def get_naver_rss(self, count=5):
        news = []
        per_cat = max(1, count // 3)
        for cat, url in NAVER_RSS.items():
            if len(news) >= count:
                break
            got = self._rss_fetch(url, "naver", cat, per_cat)
            news.extend(got)
            time.sleep(random.uniform(0.5, 1.2))
        return news[:count]

    def get_daum_rss(self, count=5):
        news = []
        per_cat = max(1, count // 3)
        for cat, url in DAUM_RSS.items():
            if len(news) >= count:
                break
            got = self._rss_fetch(url, "daum", cat, per_cat)
            news.extend(got)
            time.sleep(random.uniform(0.5, 1.2))
        return news[:count]


class NewsCollector:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def _extract_google_link(self, link: str) -> str:
        """Google News RSS 링크에서 실제 기사 URL 추출"""
        try:
            p = urlparse(link)
            if "news.google.com" in p.netloc:
                qs = parse_qs(p.query)
                if "url" in qs and qs["url"]:
                    return qs["url"][0]
        except:
            pass
        return link

    def _rss_fetch_google(self, url: str, category: str, limit: int):
        """단일 Google RSS URL에서 기사 최대 limit개 가져오기"""
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            root = ET.fromstring(r.text)
            items = []
            for item in root.findall(".//item")[:limit * 3]:
                title = self.clean_news_title(item.findtext("title") or "")
                link = (item.findtext("link") or "").strip()
                link = self._extract_google_link(link)
                if self.is_valid_news(title, link, items):
                    items.append({
                        "title": title,
                        "url": link,
                        "date": datetime.now().strftime("%Y.%m.%d"),
                        "category": category,
                        "source": "google"
                    })
            return items[:limit]
        except Exception as e:
            print(f"Google RSS 수집 오류: {e}")
            return []

    def get_google_rss(self, count=5):
        """카테고리별 Google News RSS에서 고르게 수집"""
        news = []
        per_cat = max(1, count // max(1, len(GOOGLE_RSS_QUERIES)))
        for cat, queries in GOOGLE_RSS_QUERIES.items():
            if len(news) >= count:
                break
            got_cat = 0
            for q in queries:
                if got_cat >= per_cat or len(news) >= count:
                    break
                rss_url = f"https://news.google.com/rss/search?q={quote(q)}&hl=ko&gl=KR&ceid=KR:ko"
                got = self._rss_fetch_google(rss_url, cat, limit=per_cat - got_cat)
                news.extend(got)
                got_cat += len(got)
                time.sleep(random.uniform(0.4, 1.0))
        return news[:count]

    
    def get_naver_news(self, category='society', count=5):
        """네이버 뉴스에서 카테고리별 뉴스 수집"""
        try:
            # 네이버 뉴스 카테고리 코드
            category_codes = {
                'society': '102',  # 사회
                'economy': '101',  # 경제  
                'culture': '103'   # 생활/문화
            }
            
            news_list = []
            
            for cat_name, cat_code in category_codes.items():
                if len(news_list) >= count:
                    break
                    
                try:
                    # 네이버 뉴스 메인 페이지에서 헤드라인 뉴스 수집
                    url = f'https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1={cat_code}'
                    
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 다양한 뉴스 섹션에서 수집
                    news_selectors = [
                        '.cluster_body .cluster_text a',  # 메인 클러스터
                        '.list_body .list_text a',        # 리스트 형태
                        '.headline .hdline_article_tit',  # 헤드라인
                        '.mlist2 .list_text a'            # 추가 리스트
                    ]
                    
                    collected_from_category = 0
                    max_per_category = max(1, count // 3)  # 카테고리당 최대 수집 개수
                    
                    for selector in news_selectors:
                        if collected_from_category >= max_per_category:
                            break
                            
                        items = soup.select(selector)[:5]  # 각 섹션에서 최대 5개
                        
                        for item in items:
                            if collected_from_category >= max_per_category or len(news_list) >= count:
                                break
                                
                            try:
                                title = item.get_text(strip=True)
                                link = item.get('href', '')
                                
                                if not title or not link:
                                    continue
                                
                                # 링크 정규화
                                if link.startswith('/'):
                                    link = f'https://news.naver.com{link}'
                                elif not link.startswith('http'):
                                    continue
                                
                                # 제목 정리
                                title = self.clean_news_title(title)
                                
                                # 중복 및 품질 검사
                                if self.is_valid_news(title, link, news_list):
                                    news_list.append({
                                        'title': title,
                                        'url': link,
                                        'date': datetime.now().strftime('%Y.%m.%d'),
                                        'category': cat_name,
                                        'source': 'naver'
                                    })
                                    collected_from_category += 1
                                    
                            except Exception as item_error:
                                continue
                    
                    # 요청 간격 조절
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as category_error:
                    print(f"네이버 카테고리 {cat_name} 수집 오류: {category_error}")
                    continue
            
            return news_list[:count]
            
        except Exception as e:
            print(f"네이버 뉴스 수집 오류: {e}")
            return self.get_fallback_news()[:count]
    
    def get_daum_news(self, count=5):
        """다음 뉴스에서 뉴스 수집"""
        try:
            news_list = []
            categories = ['society', 'economic', 'culture']
            
            for category in categories:
                if len(news_list) >= count:
                    break
                    
                try:
                    url = f'https://news.daum.net/breakingnews/{category}'
                    
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 다음 뉴스 구조에 맞는 셀렉터
                    news_selectors = [
                        '.list_news2 .item_issue .link_txt',
                        '.list_news .item_news .link_txt',
                        '.box_g .list_news .link_txt'
                    ]
                    
                    max_per_category = max(1, count // 3)
                    collected = 0
                    
                    for selector in news_selectors:
                        if collected >= max_per_category:
                            break
                            
                        items = soup.select(selector)[:3]
                        
                        for item in items:
                            if collected >= max_per_category or len(news_list) >= count:
                                break
                                
                            try:
                                title = item.get_text(strip=True)
                                link = item.get('href', '')
                                
                                if not title or not link:
                                    continue
                                
                                # 링크 정규화
                                if link.startswith('/'):
                                    link = f'https://news.daum.net{link}'
                                
                                # 제목 정리
                                title = self.clean_news_title(title)
                                
                                # 중복 및 품질 검사
                                if self.is_valid_news(title, link, news_list):
                                    # 다음 카테고리명을 표준 카테고리로 변환
                                    standard_category = {
                                        'society': 'society',
                                        'economic': 'economy', 
                                        'culture': 'culture'
                                    }.get(category, 'society')
                                    
                                    news_list.append({
                                        'title': title,
                                        'url': link,
                                        'date': datetime.now().strftime('%Y.%m.%d'),
                                        'category': standard_category,
                                        'source': 'daum'
                                    })
                                    collected += 1
                                    
                            except Exception as item_error:
                                continue
                    
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as category_error:
                    print(f"다음 뉴스 카테고리 {category} 오류: {category_error}")
                    continue
            
            return news_list[:count]
            
        except Exception as e:
            print(f"다음 뉴스 수집 오류: {e}")
            return []
    
    def get_fallback_news(self):
        """크롤링 실패 시 기본 뉴스"""
        today = datetime.now().strftime('%Y.%m.%d')
        
        fallback_news = [
            {
                'title': '개인정보보호법 개정안 주요 내용 및 기업 대응 방안',
                'url': 'https://www.law.go.kr',
                'date': today,
                'category': 'society',
                'source': 'fallback'
            },
            {
                'title': '중소기업 법률 지원 확대, 무료 상담 서비스 확대 시행',
                'url': 'https://www.mss.go.kr',
                'date': today,
                'category': 'economy',
                'source': 'fallback'
            },
            {
                'title': '디지털 유산 상속 관련 법률 개정 논의 본격화',
                'url': 'https://www.moleg.go.kr',
                'date': today,
                'category': 'culture',
                'source': 'fallback'
            },
            {
                'title': '온라인 계약서 법적 효력 인정 범위 대폭 확대',
                'url': 'https://www.korea.kr',
                'date': today,
                'category': 'economy',
                'source': 'fallback'
            },
            {
                'title': '소상공인 법률 상담 신청 급증, 전문가 조언의 중요성 부각',
                'url': 'https://www.sbc.or.kr',
                'date': today,
                'category': 'society',
                'source': 'fallback'
            },
            {
                'title': '전자상거래 분쟁 해결 절차 간소화 및 소비자 보호 강화',
                'url': 'https://www.kca.go.kr',
                'date': today,
                'category': 'economy',
                'source': 'fallback'
            },
            {
                'title': '원격근무 관련 노동법 적용 기준 명확화',
                'url': 'https://www.moel.go.kr',
                'date': today,
                'category': 'society',
                'source': 'fallback'
            }
        ]
        
        return fallback_news
    
    def clean_news_title(self, title):
        """뉴스 제목 정리"""
        if not title:
            return ""
            
        # 불필요한 문자 제거
        title = re.sub(r'\[.*?\]', '', title)  # 대괄호 내용 제거
        title = re.sub(r'\(.*?\)', '', title)  # 소괄호 내용 제거 (선택적)
        title = re.sub(r'<.*?>', '', title)   # HTML 태그 제거
        title = re.sub(r'\s+', ' ', title)    # 연속 공백 정리
        title = title.strip()
        
        # 제목 길이 제한
        if len(title) > 100:
            title = title[:97] + "..."
        
        return title
    
    def is_valid_news(self, title, url, existing_news):
        """뉴스 유효성 검사"""
        if not title or not url:
            return False
        
        # 최소 길이 검사
        if len(title) < 10:
            return False
        
        # 중복 제목 검사
        for news in existing_news:
            if news['title'] == title:
                return False
            
            # 제목 유사성 검사 (간단한 버전)
            if self.similarity(title, news['title']) > 0.8:
                return False
        
        # 부적절한 키워드 필터링
        spam_keywords = ['광고', '홍보', '이벤트', '할인', '쿠폰', '바로가기']
        for keyword in spam_keywords:
            if keyword in title:
                return False
        
        # URL 유효성 검사
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
        except:
            return False
        
        return True
    
    def similarity(self, text1, text2):
        """두 텍스트의 유사도 계산 (간단한 버전)"""
        if not text1 or not text2:
            return 0
        
        # 단어 단위로 분할
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        # 자카드 유사도 계산
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0
        
        return len(intersection) / len(union)
    
    def enhance_news_with_keywords(self, news_items):
        """뉴스에 법률 관련 키워드 기반 중요도 추가"""
        legal_keywords = {
            'high': ['법원', '판결', '대법원', '헌법재판소', '개정', '시행', '의무화'],
            'medium': ['정책', '제도', '규정', '기준', '절차', '신설', '변경'],
            'low': ['논의', '검토', '계획', '예정', '발표', '공개']
        }
        
        enhanced_news = []
        
        for item in news_items:
            enhanced_item = item.copy()
            title = item['title']
            
            # 중요도 점수 계산
            importance_score = 0
            
            for level, keywords in legal_keywords.items():
                for keyword in keywords:
                    if keyword in title:
                        if level == 'high':
                            importance_score += 3
                        elif level == 'medium':
                            importance_score += 2
                        else:
                            importance_score += 1
            
            enhanced_item['importance'] = min(importance_score, 5)  # 최대 5점
            enhanced_news.append(enhanced_item)
        
        # 중요도 순으로 정렬
        enhanced_news.sort(key=lambda x: x.get('importance', 0), reverse=True)
        
        return enhanced_news
    
    def collect_weekly_news(self, count=5):
        """주간 뉴스 수집 (Google RSS 우선)"""
        print("법률 관련 뉴스 수집을 시작합니다...")

        all_news = []

        # 1) Google News RSS 우선
        g = self.get_google_rss(count=count)
        all_news.extend(g)
        print(f"Google RSS: {len(g)}개")

        # 2) 부족하면 기존 HTML 크롤러 보충(있으면 사용)
        if len(all_news) < count:
            try:
                need = count - len(all_news)
                extra = self.get_naver_news(count=need)
                all_news.extend(extra)
                print(f"네이버 HTML: {len(extra)}개")
            except Exception as e:
                print("네이버 HTML 수집 실패:", e)

        if len(all_news) < count:
            try:
                need = count - len(all_news)
                extra = self.get_daum_news(count=need)
                all_news.extend(extra)
                print(f"다음 HTML: {len(extra)}개")
            except Exception as e:
                print("다음 HTML 수집 실패:", e)

        # 3) 그래도 부족하면 fallback
        if len(all_news) < count:
            fallback = self.get_fallback_news()
            all_news.extend(fallback[:count - len(all_news)])
            print("fallback으로 보충")

        # 중복 제거
        unique, seen = [], set()
        for it in all_news:
            if it["title"] not in seen:
                unique.append(it)
                seen.add(it["title"])

        # 중요도 점수 후 상위 N개
        enhanced = self.enhance_news_with_keywords(unique)
        final = enhanced[:count]
        print(f"최종 {len(final)}개 뉴스 수집 완료")
        return final




    
    def get_news_by_keyword(self, keyword, count=3):
        """특정 키워드로 뉴스 검색 (향후 확장용)"""
        try:
            # 네이버 뉴스 검색 API 또는 검색 페이지 활용
            search_url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_list = []
            items = soup.select('.news_tit')[:count]
            
            for item in items:
                try:
                    title = item.get_text(strip=True)
                    link = item.get('href', '')
                    
                    if title and link:
                        news_list.append({
                            'title': self.clean_news_title(title),
                            'url': link,
                            'date': datetime.now().strftime('%Y.%m.%d'),
                            'category': 'search',
                            'source': 'naver_search',
                            'keyword': keyword
                        })
                except:
                    continue
            
            return news_list
            
        except Exception as e:
            print(f"키워드 검색 오류: {e}")
            return []

# 테스트 함수
if __name__ == "__main__":
    collector = NewsCollector()
    
    print("=== 뉴스 수집 테스트 시작 ===")
    news = collector.collect_weekly_news(5)
    
    print(f"\n수집된 뉴스 {len(news)}개:")
    for i, item in enumerate(news, 1):
        print(f"\n{i}. [{item.get('category', 'unknown').upper()}] {item['title']}")
        print(f"   URL: {item['url']}")
        print(f"   날짜: {item['date']} | 출처: {item.get('source', 'unknown')}")
        if 'importance' in item:
            print(f"   중요도: {item['importance']}/5")
    
    print("\n=== 뉴스 수집 테스트 완료 ===")