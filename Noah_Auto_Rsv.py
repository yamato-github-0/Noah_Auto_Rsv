import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def click_button_safely(driver, button, button_name, max_attempts=10):
    for attempt in range(max_attempts):
        try:
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable(button)
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
            time.sleep(5)
            logging.info(f"{button_name}ボタンまでスクロールしました（試行 {attempt + 1}）")
            for click_method in ['normal', 'action_chains', 'javascript']:
                try:
                    if click_method == 'normal':
                        button.click()
                    elif click_method == 'action_chains':
                        ActionChains(driver).move_to_element(button).click().perform()
                    else:
                        driver.execute_script("arguments[0].click();", button)
                    logging.info(f"{button_name}ボタンを{click_method}でクリックしました（試行 {attempt + 1}）")
                    time.sleep(5)
                    return True
                except Exception as e:
                    logging.warning(f"{click_method}クリックに失敗しました（試行 {attempt + 1}）: {str(e)}")
        except Exception as e:
            logging.error(f"{button_name}ボタンのクリック中にエラーが発生しました（試行 {attempt + 1}）: {str(e)}")
        
        if attempt < max_attempts - 1:
            logging.info(f"{button_name}ボタンのクリックを再試行します（{attempt + 2}/{max_attempts}）")
            time.sleep(5)
    
    logging.error(f"{button_name}ボタンのクリックが{max_attempts}回失敗しました")
    return False

def studio_noah_login_and_book(username, password, date, start_time, end_time, studio_location, preferred_studio, practice_type):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36")
    
    service = Service('/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        logging.info("ウェブサイトにアクセスしています...")
        driver.get("https://www.studionoah.jp/")
        
        logging.info("ログインボタンをクリックしています...")
        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "login_btn_pc"))
        )
        click_button_safely(driver, login_button, "ログイン")
        
        logging.info("ログイン情報を入力しています...")
        email_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "id_text"))
        )
        email_field.send_keys(username)
        
        password_field = driver.find_element(By.ID, "pass_text")
        password_field.send_keys(password)
        
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "weblgnbtn"))
        )
        click_button_safely(driver, submit_button, "ログイン送信")
        
        logging.info("ログイン成功の確認を行っています...")
        WebDriverWait(driver, 20).until(
            EC.url_contains("https://www.studionoah.jp/noahweb/Webs/loggedmainpage")
        )
        logging.info("ログイン成功！")
        
        time.sleep(5)
        
        logging.info("BOOKINGページを開いています...")
        booking_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "booking_btn_pc"))
        )
        click_button_safely(driver, booking_button, "BOOKING")
        
        time.sleep(10)
        
        logging.info(f"日付を選択しています: {date}")
        date_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "searchdate"))
        )
        driver.execute_script(f"arguments[0].value = '{date}'", date_field)
        
        logging.info(f"開始時間を選択しています: {start_time}")
        start_time_select = Select(WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "start_time"))
        ))
        start_time_select.select_by_value(start_time)
        
        logging.info(f"終了時間を選択しています: {end_time}")
        end_time_select = Select(WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "end_time"))
        ))
        end_time_select.select_by_value(end_time)
        
        logging.info("検索を実行しています...")
        search_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'この条件で検索')]]"))
        )
        click_button_safely(driver, search_button, "検索")
        
        time.sleep(15)
        
        available_studios = driver.find_elements(By.XPATH, "//div[contains(@class, 'result_cat_box')]")
        
        if not available_studios:
            logging.warning("result_cat_boxクラスのスタジオが見つかりません。別の方法で検索を試みます。")
            available_studios = driver.find_elements(By.XPATH, "//div[contains(@class, 'studio_list_box')]")
        
        if not available_studios:
            logging.error("利用可能なスタジオが見つかりません。ページの構造が変更された可能性があります。")
            driver.save_screenshot("no_studios_available.png")
            return
        
        logging.info(f"利用可能なスタジオ数: {len(available_studios)}")
        
        preferred_studio_found = False
        for index, studio in enumerate(available_studios, start=1):
            try:
                studio_loc = studio.find_element(By.XPATH, ".//span[contains(@class, 'sr_st_locate')]").text
                studio_name = studio.find_element(By.XPATH, ".//span[contains(@class, 'sr_st_name')]").text
                logging.info(f"{index}. 利用可能: {studio_loc} {studio_name}")
                
                if studio_loc == studio_location and preferred_studio in studio_name:
                    preferred_studio_found = True
                    logging.info(f"希望のスタジオが見つかりました: {studio_loc} {studio_name}")
                    book_button = studio.find_element(By.XPATH, ".//span[@id='studio_reseve_btn']")
                    click_button_safely(driver, book_button, "WEB予約")
                    break
            except NoSuchElementException:
                logging.warning(f"スタジオ {index} の情報を取得できませんでした。スキップします。")
                continue
        
        if not preferred_studio_found:
            logging.warning(f"希望のスタジオ（{studio_location} {preferred_studio}）は利用できません。")
            driver.save_screenshot("preferred_studio_not_found.png")
            return
        
        logging.info(f"練習タイプを選択しています: {practice_type}")
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "SysOrderChargeType"))
            )
            charge_type_select = Select(driver.find_element(By.ID, "SysOrderChargeType"))
            
            options = [option.text for option in charge_type_select.options]
            if practice_type in options:
                charge_type_select.select_by_visible_text(practice_type)
            else:
                raise ValueError(f"練習タイプ '{practice_type}' はオプションに存在しません。")
        except (NoSuchElementException, TimeoutException, ValueError) as e:
            logging.error(f"練習タイプの入力を失敗しました: {str(e)}")
            driver.save_screenshot("select_practice_type_error.png")
            return

        logging.info("最終確認画面に進みます...")
        try:
            WebDriverWait(driver, 90).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            confirm_button_xpath = "//input[@type='button' and @value='最終確認画面へ']"
            confirm_button = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, confirm_button_xpath))
            )
            
            if not click_button_safely(driver, confirm_button, "最終確認画面へ"):
                raise Exception("最終確認画面へ進むボタンのクリックに失敗しました")

            WebDriverWait(driver, 90).until(
                EC.url_contains("https://www.studionoah.jp/noahweb/sysOrders/orderbooking")
            )
            logging.info("最終確認画面に正しく遷移しました")

            logging.info("'予約を確定する'ボタンを探しています...")
            
            WebDriverWait(driver, 90).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            submit_button_xpath = "//input[@id='order_determine_btn']"
            submit_button = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, submit_button_xpath))
            )
            
            if not click_button_safely(driver, submit_button, "予約を確定する", max_attempts=10):
                raise Exception("予約を確定するボタンのクリックが10回失敗しました")

            try:
                WebDriverWait(driver, 180).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), '予約完了')]")),
                        EC.url_contains("reservation_complete")
                    )
                )
                logging.info("予約が完了しました！")
            except TimeoutException:
                logging.error("予約完了ページが表示されませんでした。")
                driver.save_screenshot("reservation_not_completed.png")
                
                logging.info(f"現在のURL: {driver.current_url}")
                logging.info(f"ページタイトル: {driver.title}")
                
                try:
                    main_content = driver.find_element(By.TAG_NAME, "main").text
                    logging.info(f"メインコンテンツ: {main_content[:500]}...")
                except:
                    logging.error("メインコンテンツを取得できませんでした。")

                try:
                    error_messages = driver.find_elements(By.CLASS_NAME, "error-message")
                    if error_messages:
                        for msg in error_messages:
                            logging.error(f"エラーメッセージ: {msg.text}")
                except:
                    logging.error("エラーメッセージの確認に失敗しました。")

        except Exception as e:
            logging.error(f"予約確定プロセス中にエラーが発生しました: {str(e)}")
            driver.save_screenshot("reservation_process_error.png")
            with open("page_source_error.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logging.info("エラー時のページソースを保存しました: page_source_error.html")
            
            try:
                submit_button = driver.find_element(By.ID, "order_determine_btn")
                logging.info(f"'予約を確定する'ボタンの状態: 表示={submit_button.is_displayed()}, 有効={submit_button.is_enabled()}")
                
                for attr in ['id', 'class', 'onclick', 'type', 'value']:
                    logging.info(f"ボタンの{attr}: {submit_button.get_attribute(attr)}")
                
            except:
                logging.error("'予約を確定する'ボタンの状態を確認できませんでした。")
            
            return

    except Exception as e:
        logging.error(f"予期せぬエラーが発生しました: {str(e)}")
        driver.save_screenshot("unexpected_error.png")
        with open("page_source_unexpected.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info("予期せぬエラー時のページソースを保存しました: page_source_unexpected.html")
    finally:
        input("処理が完了しました。ブラウザを閉じるにはEnterキーを押してください...")
        driver.quit()

if __name__ == "__main__":
    username = "xxxx"
    password = "xxxx" #パスワードを変更した場合は注意
    date = "yyyy/mm/dd" #キャンセル可能な日時か、予約可能な日時か注意
    start_time = "hh:mm" #00分開始か30分開始かに注意
    end_time = "hh:mm"
    studio_location = "新宿"
    preferred_studio = "CSst+Sub" #表記揺れに注意「CSst+Sub」「Cst+Sub」など
    practice_type = "通常料金" #「通常料金」「個人練習１人」「個人練習２人」のいずれかを入力
    studio_noah_login_and_book(username, password, date, start_time, end_time, studio_location, preferred_studio, practice_type)