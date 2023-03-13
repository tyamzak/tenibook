from playwright.sync_api import Playwright, sync_playwright, expect
from time import sleep
import yaml
from datetime import datetime as dt, timedelta
import re

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

def list_target_dates():

    today = dt.today()  # 本日の日付
    last_day_of_month = today.replace(day=28) + timedelta(days=4)  # 本日が属する月の最後の日付

    dates = []  # 月曜と木曜の日付を格納するリスト

    # 本日から本日が属する月の最後の日付までループ
    current_date = today.replace(day=1)
    while current_date <= last_day_of_month:
        # 月曜日の場合、日付をリストに追加
        if current_date.weekday() == 0:
            dates.append(current_date.strftime('%Y/%m/%d'))
            
        # 木曜日の場合、日付をリストに追加
        if current_date.weekday() == 3:
            dates.append(current_date.strftime('%Y/%m/%d'))
        
        current_date += timedelta(days=1)  # 翌日の日付に進む

    print("予約対象の日付")
    print(dates)

    return(dates)

def is_valid_time(time_str):
    # 正規表現を使用して、文字列が "H:M" 形式であることを確認
    if re.match(r'^\d{1,2}:\d{2}$', time_str):
        return True
    else:
        return False

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    def login(page):
        userid = str(config.get('userid'))
        password = str(config.get('password'))
        page.goto("https://www.cm1.eprs.jp/kariya/web/view/user/homeIndex.html")
        page.click("#login > img")
        page.locator('#userid').type(userid)
        page.locator('#passwd').type(password)
        page.locator('#doLogin').click()

    def page_confirmation(page,):
        # 利用可能な施設と空き状況
        pass
    def mypage_main(page):

        # ページがロードされるのを待つ
        page.wait_for_load_state('networkidle')
        page.locator('//*[@id="isBtnOn02"]').click()
        

        # page.get_by_alt_text('マイページ').click()

        # ページがロードされるのを待つ
        page.wait_for_load_state('networkidle')
        #目的からをクリック
        # page.locator("#goPurposeSearch > img").click()

        #利用日時から探すをクリック
        page.locator("#goDateSearch > img").click()


    def riyounichiji_kensaku(page, purpose:str, year_num:str,month_num:str,day_num:str):

        # ページがロードされるのを待つ
        page.wait_for_load_state('networkidle')

        #年月日をクリック
        page.locator('//*[@id="year"]').select_option(year_num)
        page.locator('//*[@id="month"]').select_option(month_num)
        page.locator('//*[@id="day"]').select_option(day_num)

        #時間をクリック
        page.locator('//*[@id="sHour"]').select_option('9')
        page.locator('//*[@id="sMinute"]').select_option('0')
        page.locator('//*[@id="eHour"]').select_option('12')
        page.locator('//*[@id="eMinute"]').select_option('0')


        #ソフトテニスをクリック
        # page.get_by_label("ソフトテニス").click()

        # purposeをクリック
        page.get_by_label(purpose).click()

        # 上記の内容で検索をクリック
        page.locator('//*[@id="doDateSearch"]').click()
    
    def akijoukyou(page,config,target_exists = False):
        """特定の日付において空いている時間帯をチェックし、カートに入れる
            コンフィグの優先コートが無いか最初に探し、戻ってくる。
        """

        #複数ページ用のループ
        while True:
            # ページがロードされるのを待つ
            page.wait_for_load_state('networkidle')

            # リスト全体を取得
            listitems = page.locator('//*[@id="isNotEmptyPager"]/table')

            # 無かったら終了する
            listnum = listitems.count()
            if listnum == 0:
                print('予約対象が見つかりませんでした')
                return False
            flg_add_cart = False

            #場所ごとのループ
            for i in range(0,listnum):
                #tr = 1 部屋名エリア
                place_name = listitems.nth(i).locator('//*[@id="bnamem"]').inner_text()
                if target_exists:
                    #優先確保場所がある場合は、合致チェック
                    if place_name in config.get('coats'):
                        print(f'{place_name}の空きを発見')
                    else:
                        continue

                child_place_name = listitems.nth(i).locator('//*[@id="inamem"]').inner_text()
                #tr = 2 時間帯エリア
                timeranges = listitems.nth(i).locator('//*[@class="time-table1"]')
                chkboxes = listitems.nth(i).locator('//*[@class="time-table2"]')
                timeranges_num = timeranges.count()
                #時間帯ごとのループ
                for j in range(0,timeranges_num):

                    #単数字形式かどうか確認する
                    if timeranges.nth(j).locator('//*[@id="tzonename"]').count():
                        timezone_name = timeranges.nth(j).locator('//*[@id="tzonename"]').inner_text()
                        starttime = timeranges.nth(j).locator('//*[@id="stimelbl"]').inner_text()
                        endtime = timeranges.nth(j).locator('//*[@id="etimelbl"]').inner_text()
                        #9:00形式の場合
                        
                        if is_valid_time(starttime):
                            #時間が一致する場合
                            if dt.strptime(starttime,'%H:%M').time() >= dt.strptime(config.get('starttime'),'%H:%M').time() and \
                            dt.strptime(endtime,'%H:%M').time() <= dt.strptime(config.get('endtime'),'%H:%M').time():
                                
                                #チェックボックスを取得する
                                chkbox = chkboxes.nth(j).locator('//*[@id="emptyStateIcon"]')
                                # 状態の取得
                                chkstate = chkbox.get_attribute('alt')
                                if chkstate == '空き':
                                    # クリックする
                                    chkbox.click()
                                    flg_add_cart = True
                                    # print(timezone_name, starttime, endtime)
                    else:
                        #単数字形式の場合、9と11が空いていればクリックする
                        hour_str = timeranges.nth(j).inner_text()
                        starthour_int = dt.strptime(config.get('starttime'),'%H:%M').hour
                        endhour_int = dt.strptime(config.get('endtime'),'%H:%M').hour
                        #文字列が数字認識可能か調査し、
                        if hour_str.isdigit():
                            hour_int = int(hour_str)
                        else:
                            continue

                        if hour_int >= starthour_int and \
                        hour_int <= endhour_int:
                            
                            #チェックボックスを取得する
                            chkbox = chkboxes.nth(j).locator('//*[@id="emptyStateIcon"]')

                            # 状態の取得
                            chkstate = chkbox.get_attribute('alt')
                            if chkstate == '空き':
                                # クリックする
                                chkbox.click()
                                flg_add_cart = True


                #カートに追加するものがある場合            
                if flg_add_cart:
                    #予約カートに追加
                    btn_addcart = listitems.nth(i).locator('//*[@id="doAddCart"]')
                    btn_addcart.click()
                    #この日は終了
                    return    True
                
            btn_nextpage = page.locator('//*[@id="isFooterNext"]')

            if btn_nextpage.count() > 0:   
                print('次のページに遷移します')
                btn_nextpage.click()
            else:
                print('予約対象が見つかりませんでした')
                # ページをはじめに戻す
                elem = page.locator('//*[@id="isFooter"]/table/tbody/tr/td')
                if elem.count():
                    elem2 = elem.locator('//*[@id="pageDisp"]')
                    if elem2.count():
                        elem3 = elem2.get_by_text('1')
                        elem3.nth(0).click() 
                return False
            
    def cart_to_input_detail(page):
        """予約カートクリックから、詳細情報入力画面まで遷移する
        """
        # 予約カートの内容を確認をクリック
        page.locator('//*[@id="jumpRsvCartList"]').click()

        # ページがロードされるのを待つ
        page.wait_for_load_state('networkidle')

        # 予約確定の手続きへをクリック
        page.locator('//*[@id="doCartDetails"]').click()

        # ページがロードされるのを待つ
        page.wait_for_load_state('networkidle')
        
        # 利用条件に同意するをクリック
        page.locator('//*[@id="yeslabel"]').click()

        # 詳細情報の入力へをクリック
        page.locator('//*[@id="doInputDetails"]').click()

        # ページがロードされるのを待つ
        page.wait_for_load_state('networkidle')

    def input_detail_to_Fix(page,config):
        #目的・利用人数は複数対応にする
        purposes = page.locator('//*[@id="purposeDetails"]')
        numuses = page.locator('//*[@id="useCnt"]')

        numpurpses = purposes.count()
        for i in range(0,numpurpses):
            purposes.nth(i).fill('ソフトテニス　練習')
            numuses.nth(i).fill('8')

        # ページがロードされるのを待つ
        page.wait_for_load_state('networkidle')

        #予約を確認するをクリックする
        page.locator('//*[@id="doConfirm"]').click()
        
        #予約を確定するをクリック　"!!!"デバッグ中はコメントアウト！
        if config.get('debug'):
            print('デバッグ中：予約の確定を行いません')
        else:
            print('予約確定')
            page.locator('//*[@id="doOnceLockFix"]').click()

        # ページがロードされるのを待つ
        page.wait_for_load_state('networkidle')

    target_list = list_target_dates()
    login(page)

    for i in target_list:
        print(f'{i}の予約確認')
        target_day = dt.strptime(i, '%Y/%m/%d')
        year_num = str(target_day.year)
        month_num = str(target_day.month)
        day_num = str(target_day.day)

        

        #日時で繰り返し
        mypage_main(page)
        purpose = config.get('purpose')
        riyounichiji_kensaku(page,purpose,year_num,month_num,day_num)
        # riyounichiji_kensaku(page,"ソフトテニス",year_num,month_num,day_num)

        #最初は施設指定、うまく行かなかったら無差別に予約する
        print('優先検索施設を探します')
        if akijoukyou(page,config,target_exists=True) is False:
            
            print('無差別に探します')
            if akijoukyou(page,config,target_exists=False) is False:

                continue

        cart_to_input_detail(page)
        input_detail_to_Fix(page,config)
    

    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)


from playwright.sync_api import Playwright, sync_playwright, expect




