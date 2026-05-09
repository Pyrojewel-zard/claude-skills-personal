#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome无头模式全自动批量下载Sci-Hub论文
基于测试成功的流程，自动处理人机验证和下载
"""
import os
import csv
import time
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 配置
SCI_HUB_DOMAIN = "https://sci-hub.ru"
INPUT_CSV = Path("/tmp/doi_2021_and_earlier.csv")
DOWNLOAD_DIR = Path.home() / "Downloads" / "SciHub_Papers"  # 下载到用户目录的SciHub_Papers文件夹
LOG_FILE = DOWNLOAD_DIR / "download_log.csv"
MAX_RETRIES = 2  # 每个DOI最多重试次数
MIN_DELAY = 3  # 最小间隔时间(秒)
MAX_DELAY = 5  # 最大间隔时间(秒)
PAGE_TIMEOUT = 30  # 页面加载超时时间(秒)

def init_headless_chrome():
    """初始化无头模式Chrome"""
    chrome_options = Options()

    # 无头模式配置
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    # 反爬配置，隐藏自动化特征
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # 下载配置
    prefs = {
        "download.default_directory": str(DOWNLOAD_DIR.absolute()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,
        "plugins.always_open_pdf_externally": True,  # 直接下载PDF而不是打开
        "profile.managed_default_content_settings.images": 1,  # 加载图片，避免反爬检测
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # 自定义请求头
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    chrome_options.add_argument("accept-language=zh-CN,zh;q=0.9,en;q=0.8")

    # 启动浏览器
    driver = webdriver.Chrome(options=chrome_options)

    # 移除webdriver特征
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # 设置页面加载超时
    driver.set_page_load_timeout(PAGE_TIMEOUT)

    return driver

def sanitize_filename(doi):
    """将DOI转换为合法文件名"""
    return doi.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_') + ".pdf"

def is_download_complete(filename, timeout=60):
    """检查文件是否下载完成"""
    filepath = DOWNLOAD_DIR / filename
    start_time = time.time()

    while time.time() - start_time < timeout:
        if filepath.exists() and os.path.getsize(filepath) > 0:
            # 检查是否有临时下载文件
            if not (DOWNLOAD_DIR / (filename + '.crdownload')).exists():
                return True
        time.sleep(1)
    return False

def download_paper(driver, doi, title, item_key):
    """下载单篇论文"""
    filename = sanitize_filename(doi)
    filepath = DOWNLOAD_DIR / filename

    # 检查是否已经下载过
    if filepath.exists():
        print(f"✅ 已存在，跳过: {doi}")
        return "skipped", str(filepath)

    try:
        url = f"{SCI_HUB_DOMAIN}/{doi}"
        print(f"\n🔍 正在处理: {doi}")
        print(f"📄 标题: {title[:80]}...")

        # 访问页面
        driver.get(url)

        # 检查是否有人机验证
        try:
            # 查找"No"按钮
            no_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'No')]"))
            )
            no_button.click()
            print("🤖 通过人机验证")
            time.sleep(2)  # 等待验证后页面跳转
        except TimeoutException:
            # 没有验证页面，继续
            pass

        # 等待页面加载完成
        WebDriverWait(driver, PAGE_TIMEOUT).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # 查找PDF下载链接
        pdf_url = None

        # 方法1：查找包含.pdf的链接
        try:
            pdf_link = driver.find_element(By.XPATH, "//a[contains(@href, '.pdf')]")
            pdf_url = pdf_link.get_attribute('href')
        except NoSuchElementException:
            pass

        # 方法2：查找embed或iframe
        if not pdf_url:
            try:
                embed = driver.find_element(By.TAG_NAME, "embed")
                pdf_url = embed.get_attribute('src')
            except NoSuchElementException:
                pass

            if not pdf_url:
                try:
                    iframe = driver.find_element(By.TAG_NAME, "iframe")
                    pdf_url = iframe.get_attribute('src')
                except NoSuchElementException:
                    pass

        # 方法3：从页面源码中提取
        if not pdf_url:
            page_source = driver.page_source
            import re
            pdf_match = re.search(r'https?:\/\/[^"\s]+\.pdf[^"\s]*', page_source)
            if pdf_match:
                pdf_url = pdf_match.group(0)

        if not pdf_url:
            print(f"❌ 未找到PDF链接")
            return "failed", "No PDF URL found"

        print(f"🔗 找到PDF: {pdf_url[:80]}...")

        # 下载PDF
        driver.execute_script(f"""
            const a = document.createElement('a');
            a.href = '{pdf_url}';
            a.download = '{filename}';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        """)

        # 等待下载完成
        if is_download_complete(filename):
            print(f"✅ 下载成功: {filename}")
            return "success", str(filepath)
        else:
            print(f"❌ 下载超时")
            return "failed", "Download timeout"

    except Exception as e:
        error_msg = str(e)[:100]
        print(f"❌ 处理失败: {error_msg}")
        return "failed", error_msg

def main():
    # 创建下载目录
    DOWNLOAD_DIR.mkdir(exist_ok=True, parents=True)

    # 读取DOI列表
    if not INPUT_CSV.exists():
        print(f"❌ 错误：DOI文件不存在：{INPUT_CSV}")
        return

    papers = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            papers.append({
                'doi': row['DOI'].strip(),
                'title': row['Title'],
                'item_key': row['Item Key']
            })

    total = len(papers)
    print(f"📚 共找到 {total} 篇论文需要下载")
    print(f"💾 下载目录：{DOWNLOAD_DIR}")
    print("="*80)

    # 初始化浏览器
    print("🚀 启动无头Chrome浏览器...")
    driver = init_headless_chrome()

    # 初始化日志文件
    log_exists = LOG_FILE.exists()
    with open(LOG_FILE, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not log_exists:
            writer.writerow(['DOI', 'Title', 'Item Key', 'Status', 'Message', 'Timestamp'])

    success = 0
    failed = 0
    skipped = 0

    try:
        for i, paper in enumerate(papers, 1):
            doi = paper['doi']
            title = paper['title']
            item_key = paper['item_key']

            if not doi:
                skipped +=1
                continue

            status = "failed"
            message = ""
            filepath = ""

            # 重试机制
            for retry in range(MAX_RETRIES + 1):
                if retry > 0:
                    print(f"🔄 第 {retry} 次重试...")
                    time.sleep(MIN_DELAY)

                status, message = download_paper(driver, doi, title, item_key)

                if status == "success" or status == "skipped":
                    break

            # 统计结果
            if status == "success":
                success += 1
            elif status == "failed":
                failed += 1
            elif status == "skipped":
                skipped += 1

            # 记录日志
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(LOG_FILE, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([doi, title, item_key, status, message, timestamp])

            # 进度报告
            if i % 10 == 0 or i == total:
                print(f"\n===== 进度：{i}/{total} | 成功：{success} | 失败：{failed} | 跳过：{skipped} | 成功率：{success/(i-skipped)*100:.1f}% =====\n")

            # 随机间隔，避免被封
            if i < total and status != "skipped":
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                time.sleep(delay)

    finally:
        # 关闭浏览器
        driver.quit()

        # 最终报告
        print("\n" + "="*80)
        print("🏁 全部任务完成！")
        print(f"总论文数：{total}")
        print(f"✅ 成功下载：{success}")
        print(f"❌ 下载失败：{failed}")
        print(f"⏭️  跳过已存在：{skipped}")
        print(f"📊 成功率：{success/(total-skipped)*100:.1f}%" if (total-skipped) > 0 else "")
        print(f"💾 下载目录：{DOWNLOAD_DIR}")
        print(f"📝 日志文件：{LOG_FILE}")
        print("="*80)

if __name__ == "__main__":
    main()
