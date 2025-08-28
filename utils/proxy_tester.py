#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نظام اختبار البروكسيات الفعال
"""

import asyncio
import aiohttp
import time
import socket
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import requests
from urllib.parse import urlparse
import socks as pysocks

@dataclass
class ProxyTestResult:
    """نتيجة اختبار البروكسي"""
    proxy: str
    is_working: bool
    response_time: float
    error_message: Optional[str] = None
    country: Optional[str] = None
    anonymity: Optional[str] = None
    protocol: Optional[str] = None  # 'http' أو 'socks5h'

class ProxyTester:
    def __init__(self):
        self.test_urls = [
            'https://httpbin.org/ip',
            'https://api.ipify.org?format=json',
            'https://ipinfo.io/json',
            'https://www.tiktok.com',
            'https://api16-normal-c-alisg.ttapis.com'
        ]
        self.timeout = 10
        self.max_workers = 10

    def _parse_proxy_line(self, proxy: str) -> Tuple[str, str]:
        """إرجاع (protocol, url) مع دعم user:pass@host:port وبدون مخطط.

        - إذا كان يحتوي على مخطط http:// أو https:// أو socks5:// أو socks5h://، نعيده كما هو.
        - إذا كان يحتوي على '@' نعتبره SOCKS5H مع مصادقة: user:pass@host:port.
        - وإلا ip:port -> socks5h://ip:port ومرشح بديل http://ip:port.
        """
        p = proxy.strip()
        if p.startswith(('http://', 'https://')):
            return ('http', p)
        if p.startswith(('socks5://', 'socks5h://')):
            # طبعاً نفضّل socks5h لتمرير DNS
            return ('socks5h', p.replace('socks5://', 'socks5h://', 1))

        if '@' in p and ':' in p:
            # user:pass@host:port
            return ('socks5h', f"socks5h://{p}")

        # ip:port خام
        if ':' in p:
            # سنجرب socks5h أولاً، ويبقى http كبديل في المرشحين لاحقاً
            return ('socks5h', f"socks5h://{p}")

        # غير معروف، أعده كما هو كـ socks5h
        return ('socks5h', f"socks5h://{p}")
    
    async def test_proxy_async(self, proxy: str) -> ProxyTestResult:
        """اختبار البروكسي بشكل غير متزامن"""
        start_time = time.time()
        
        try:
            # إعداد المرشحين بناءً على التحليل
            candidates: List[Tuple[str, str]] = []  # (url, protocol)
            proto, url = self._parse_proxy_line(proxy)
            # جرّب البروتوكول المفضّل أولاً
            candidates.append((url, proto))
            # أضف بديلًا إذا كان ip:port (حاول http أيضًا)
            if '://' not in proxy and ':' in proxy:
                candidates.append((f"http://{proxy}", 'http'))

            # جرّب المرشحين
            last_error: Optional[str] = None
            for prox, proto in candidates:
                # فحص سريع عبر PySocks إذا كان SOCKS5H: اتصل بـ 8.8.8.8:53 عبر البروكسي
                if proto.startswith('socks5'):
                    quick_ok = await self._quick_socks5_tcp_check(prox)
                    if not quick_ok:
                        last_error = "فشل فحص PySocks السريع"
                        continue
                if proto == 'http':
                    http_result = await self._test_http(prox)
                    if http_result:
                        response_time = time.time() - start_time
                        return ProxyTestResult(
                            proxy=prox,
                            is_working=True,
                            response_time=response_time,
                            country=http_result.get('country'),
                            anonymity=http_result.get('anonymity'),
                            protocol='http'
                        )
                else:
                    socks_result = await self._test_socks5(prox)
                    if socks_result:
                        response_time = time.time() - start_time
                        return ProxyTestResult(
                            proxy=prox,
                            is_working=True,
                            response_time=response_time,
                            country=socks_result.get('country'),
                            anonymity=socks_result.get('anonymity'),
                            protocol='socks5h'
                        )
                last_error = "فشل اختبار البروتوكولات"
            
            return ProxyTestResult(
                proxy=proxy,
                is_working=False,
                response_time=time.time() - start_time,
                error_message=last_error or "فشل في جميع اختبارات البروتوكول"
            )
            
        except Exception as e:
            return ProxyTestResult(
                proxy=proxy,
                is_working=False,
                response_time=time.time() - start_time,
                error_message=str(e)
            )

    async def _quick_socks5_tcp_check(self, proxy_url: str, timeout: float = 5.0) -> bool:
        """اختبار سريع عبر PySocks: الاتصال بـ 8.8.8.8:53 من خلال البروكسي."""
        try:
            parsed = urlparse(proxy_url.replace('socks5h://', 'socks5://', 1))
            host = parsed.hostname
            port = parsed.port or 1080
            username = parsed.username
            password = parsed.password
            if not host or not port:
                return False
            def _tcp_test() -> bool:
                s = pysocks.socksocket()
                s.set_proxy(pysocks.SOCKS5, host, int(port), username=username, password=password)
                s.settimeout(timeout)
                try:
                    s.connect(("8.8.8.8", 53))
                    return True
                finally:
                    try:
                        s.close()
                    except Exception:
                        pass
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _tcp_test)
        except Exception:
            return False
    
    async def _test_connection(self, proxy: str) -> bool:
        """اختبار الاتصال الأساسي"""
        try:
            # تحليل البروكسي
            if proxy.startswith('socks5://') or proxy.startswith('socks5h://'):
                host, port = self._parse_socks5_proxy(proxy)
            elif proxy.startswith('http://') or proxy.startswith('https://'):
                parsed = urlparse(proxy)
                host, port = parsed.hostname, parsed.port or (80 if parsed.scheme == 'http' else 443)
            else:
                # ip:port خام
                host, port = proxy.split(':', 1)
                port = int(port)
            
            # اختبار الاتصال
            future = asyncio.get_event_loop().run_in_executor(
                None, self._test_socket_connection, host, port
            )
            return await asyncio.wait_for(future, timeout=5)
            
        except Exception as e:
            print(f"❌ خطأ في اختبار الاتصال: {e}")
            return False
    
    def _test_socket_connection(self, host: str, port: int) -> bool:
        """اختبار الاتصال عبر Socket"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _parse_socks5_proxy(self, proxy: str) -> Tuple[str, int]:
        """تحليل بروكسي SOCKS5"""
        if proxy.startswith('socks5h://'):
            proxy = proxy[10:]
        elif proxy.startswith('socks5://'):
            proxy = proxy[9:]
        
        if ':' in proxy:
            host, port = proxy.split(':', 1)
            return host, int(port)
        else:
            return proxy, 1080
    
    async def _test_http(self, proxy: str) -> Optional[Dict]:
        """اختبار البروكسي عبر HTTP"""
        if not proxy.startswith(('http://', 'https://')):
            return None
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                # اختبار مع TikTok مباشرة
                async with session.get(
                    'https://www.tiktok.com',
                    proxy=proxy,
                    ssl=False,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                ) as response:
                    if response.status == 200:
                        return {
                            'country': 'TikTok Accessible',
                            'anonymity': 'transparent'
                        }
        except Exception:
            pass
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(
                    'https://httpbin.org/ip',
                    proxy=proxy,
                    ssl=False
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'country': data.get('origin'),
                            'anonymity': 'transparent'
                        }
        except Exception:
            pass
        
        return None
    
    async def _test_socks5(self, proxy: str) -> Optional[Dict]:
        """اختبار البروكسي عبر SOCKS5"""
        try:
            # استخدام aiohttp مع SOCKS5
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                
                # اختبار مع TikTok مباشرة
                async with session.get(
                    'https://www.tiktok.com',
                    proxy=proxy,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                ) as response:
                    if response.status == 200:
                        return {
                            'country': 'TikTok Accessible',
                            'anonymity': 'socks5'
                        }
                        
        except Exception:
            pass
        
        return None
    
    async def test_multiple_proxies(self, proxies: List[str]) -> List[ProxyTestResult]:
        """اختبار عدة بروكسيات في نفس الوقت"""
        tasks = []
        for proxy in proxies:
            task = self.test_proxy_async(proxy)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # معالجة النتائج
        valid_results = []
        for result in results:
            if isinstance(result, ProxyTestResult):
                valid_results.append(result)
            else:
                print(f"خطأ في اختبار البروكسي: {result}")
        
        return valid_results
    
    def filter_working_proxies(self, results: List[ProxyTestResult], 
                              min_response_time: float = 0.0,
                              max_response_time: float = 10.0) -> List[ProxyTestResult]:
        """فلترة البروكسيات العاملة"""
        working_proxies = []
        
        for result in results:
            if (result.is_working and 
                min_response_time <= result.response_time <= max_response_time):
                working_proxies.append(result)
        
        # ترتيب حسب سرعة الاستجابة
        working_proxies.sort(key=lambda x: x.response_time)
        return working_proxies
    
    def get_proxy_stats(self, results: List[ProxyTestResult]) -> Dict:
        """الحصول على إحصائيات البروكسيات"""
        total = len(results)
        working = len([r for r in results if r.is_working])
        failed = total - working
        
        if working > 0:
            avg_response_time = sum(r.response_time for r in results if r.is_working) / working
            min_response_time = min(r.response_time for r in results if r.is_working)
            max_response_time = max(r.response_time for r in results if r.is_working)
        else:
            avg_response_time = min_response_time = max_response_time = 0
        
        return {
            'total': total,
            'working': working,
            'failed': failed,
            'success_rate': (working / total * 100) if total > 0 else 0,
            'avg_response_time': avg_response_time,
            'min_response_time': min_response_time,
            'max_response_time': max_response_time
        }
    
    def format_result_proxy(self, result: ProxyTestResult) -> str:
        """بناء نص البروكسي النهائي حسب البروتوكول المكتشف"""
        prox = result.proxy
        if result.protocol == 'http':
            if not prox.startswith(('http://', 'https://')):
                return f"http://{prox}"
            return prox
        if result.protocol == 'socks5h':
            if prox.startswith('socks5://'):
                return prox.replace('socks5://', 'socks5h://', 1)
            if not prox.startswith('socks5h://'):
                return f"socks5h://{prox}"
            return prox
        # fallback
        if prox.startswith('socks5://'):
            return prox.replace('socks5://', 'socks5h://', 1)
        return prox

# دالة مساعدة لاختبار البروكسيات
async def test_proxies(proxy_list: List[str]) -> Tuple[List[str], Dict]:
    """
    اختبار قائمة من البروكسيات
    
    Args:
        proxy_list: قائمة البروكسيات بصيغة ip:port أو socks5://ip:port
        
    Returns:
        Tuple[List[str], Dict]: (قائمة البروكسيات العاملة, إحصائيات)
    """
    tester = ProxyTester()
    
    # اختبار جميع البروكسيات
    print(f"🔍 بدء اختبار {len(proxy_list)} بروكسي...")
    results = await tester.test_multiple_proxies(proxy_list)
    
    # فلترة البروكسيات العاملة
    working_proxies = tester.filter_working_proxies(results, max_response_time=8.0)
    
    # الحصول على الإحصائيات
    stats = tester.get_proxy_stats(results)
    
    # تنسيق البروكسيات العاملة وفق البروتوكول المكتشف
    formatted_proxies = [tester.format_result_proxy(r) for r in working_proxies]
    
    return formatted_proxies, stats

if __name__ == "__main__":
    # اختبار بسيط
    test_proxies = [
        "127.0.0.1:1080",
        "192.168.1.1:1080",
        "socks5://127.0.0.1:1080"
    ]
    
    async def main():
        working, stats = await test_proxies(test_proxies)
        print(f"✅ البروكسيات العاملة: {working}")
        print(f"📊 الإحصائيات: {stats}")
    
    asyncio.run(main())