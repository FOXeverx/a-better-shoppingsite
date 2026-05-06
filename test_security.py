#!/usr/bin/env python3
"""
安全中间件测试脚本
测试 RateLimitMiddleware、UserAgentMiddleware、SecurityHeadersMiddleware
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def print_test(name, passed, message=""):
    status = f"[通过]" if passed else f"[失败]"
    print(f"{status} {name}")
    if message:
        print(f"      {message}")


def test_security_headers():
    """测试安全响应头"""
    print(f"\n=== 测试安全响应头 ===")
    
    try:
        resp = requests.get(f"{BASE_URL}/", headers=DEFAULT_HEADERS)
        
        if resp.status_code >= 400:
            print(f"服务器返回错误: {resp.status_code}")
            print(f"响应内容: {resp.text[:200]}")
            return False
        
        headers = resp.headers
        
        checks = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
        }
        
        all_passed = True
        for header, expected in checks.items():
            if header in headers and headers[header] == expected:
                print_test(f"{header} 头", True)
            else:
                print_test(f"{header} 头", False, f"期望: {expected}, 实际: {headers.get(header, '不存在')}")
                all_passed = False
        
        return all_passed
    except requests.exceptions.ConnectionError:
        print_test("连接服务器", False, "请确保服务器已启动")
        return False
    except Exception as e:
        print_test("测试异常", False, str(e))
        return False


def test_user_agent_block():
    """测试User-Agent拦截"""
    print(f"\n=== 测试User-Agent拦截 ===")
    
    test_uas = [
        ("python-requests", "python-requests/2.25.1"),
        ("curl", "curl/7.68.0"),
        ("wget", "Wget/1.20.4"),
        ("scrapy", "Scrapy/2.5.0"),
    ]
    
    all_passed = True
    for name, ua in test_uas:
        try:
            resp = requests.get(f"{BASE_URL}/", headers={"User-Agent": ua})
            
            if resp.status_code >= 500:
                print_test(f"拦截 {name}", False, f"服务器错误: {resp.status_code}")
                all_passed = False
                continue
                
            if resp.status_code == 403 and "Access denied" in resp.text:
                print_test(f"拦截 {name}", True)
            else:
                print_test(f"拦截 {name}", False, f"状态码: {resp.status_code}")
                all_passed = False
        except requests.exceptions.ConnectionError:
            print_test("连接服务器", False, "请确保服务器已启动")
            return False
    
    return all_passed


def test_user_agent_allow():
    """测试正常User-Agent放行"""
    print(f"\n=== 测试正常User-Agent放行 ===")
    
    normal_uas = [
        ("Chrome", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
        ("Firefox", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"),
    ]
    
    all_passed = True
    for name, ua in normal_uas:
        try:
            resp = requests.get(f"{BASE_URL}/", headers={"User-Agent": ua})
            if resp.status_code == 200:
                print_test(f"放行 {name}", True)
            else:
                print_test(f"放行 {name}", False, f"状态码: {resp.status_code}")
                all_passed = False
        except requests.exceptions.ConnectionError:
            print_test("连接服务器", False, "请确保服务器已启动")
            return False
    
    return all_passed


def test_rate_limit():
    """测试IP限流"""
    print(f"\n=== 测试IP限流 ===")
    
    try:
        limit = 60
        print(f"将发送 {limit + 5} 个请求测试限流...")
        
        status_codes = []
        for i in range(limit + 5):
            try:
                resp = requests.get(f"{BASE_URL}/api/product", headers=DEFAULT_HEADERS, timeout=2)
                status_codes.append(resp.status_code)
            except requests.exceptions.Timeout:
                status_codes.append(0)
            except requests.exceptions.ConnectionError:
                status_codes.append(-1)
            
            if i % 20 == 0 and i > 0:
                print(f"  已发送 {i} 请求...")
        
        if 429 in status_codes:
            print_test("触发限流", True, f"第{status_codes.index(429)+1}次请求返回429")
            print("等待2秒后再次请求测试封禁...")
            time.sleep(2)
            resp = requests.get(f"{BASE_URL}/api/product", headers=DEFAULT_HEADERS, timeout=2)
            
            if resp.status_code in [429, 403]:
                print_test("IP封禁生效", True, f"返回状态码: {resp.status_code}")
            else:
                print_test("IP封禁生效", False, f"返回状态码: {resp.status_code}")
            
            return True
        else:
            print_test("触发限流", False, f"未收到429响应，状态码: {set(status_codes)}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_test("连接服务器", False, "请确保服务器已启动")
        return False
    except Exception as e:
        print_test("测试异常", False, str(e))
        return False


def check_server():
    """检查服务器是否运行"""
    try:
        resp = requests.get(f"{BASE_URL}/", headers=DEFAULT_HEADERS, timeout=2)
        return True
    except:
        return False


def main():
    print(f"安全中间件测试")
    print(f"=" * 50)
    
    if not check_server():
        print(f"错误：无法连接到服务器 {BASE_URL}")
        print(f"请先启动服务器: uvicorn app.main:app --reload")
        sys.exit(1)
    
    results = []
    
    results.append(("安全响应头", test_security_headers()))
    results.append(("User-Agent拦截", test_user_agent_block()))
    results.append(("正常User-Agent放行", test_user_agent_allow()))
    results.append(("IP限流", test_rate_limit()))
    
    print(f"\n{'='*50}")
    print(f"测试结果汇总")
    print(f"{'='*50}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {name}")
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("所有测试通过!")
    else:
        print("部分测试失败")


if __name__ == "__main__":
    main()