import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
            st.title("🏠 Home")
    if st.session_state.get("logged_in"):
        st.success(f"{st.session_state.get('user_email')}님, 환영합니다.")

    st.markdown("""
    **Population Trends Dataset**  
    - 제공처: 통계청(KOSIS)  
    - 설명: 한국 각 광역자치단체별 연도별 인구·출생자·사망자 수 현황을 담은 데이터  
    - 주요 변수:  
      - `Year` (연도)  
      - `지역` (광역자치단체 명)  
      - `인구` (총 인구 수)  
      - `출생아수(명)` (해당 연도 출생자 수)  
      - `사망자수(명)` (해당 연도 사망자 수)
    """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trend EDA")

        # 1) Upload
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv")
            st.stop()

        # 2) Read & clean
        orig_df = pd.read_csv(uploaded, dtype=str)
        orig_df.columns = orig_df.columns.str.strip()
        orig_df = orig_df.replace('-', '0')
        orig_df['Year']       = orig_df['연도'].astype(int)
        orig_df['Population'] = pd.to_numeric(orig_df['인구'], errors='coerce')
        orig_df['Births']     = pd.to_numeric(orig_df['출생아수(명)'], errors='coerce')
        orig_df['Deaths']     = pd.to_numeric(orig_df['사망자수(명)'], errors='coerce')

        # 3) Prepare regional DataFrame (exclude nationwide)
        region_df = orig_df[orig_df['지역'] != '전국'].copy()

        # 4) Pivot on Korean region names, then rename columns to English
        region_map = {
            '서울특별시':'Seoul','부산광역시':'Busan','대구광역시':'Daegu',
            '인천광역시':'Incheon','광주광역시':'Gwangju','대전광역시':'Daejeon',
            '울산광역시':'Ulsan','세종특별자치시':'Sejong','세종':'Sejong',
            '경기도':'Gyeonggi','강원도':'Gangwon','충청북도':'Chungbuk',
            '충청남도':'Chungnam','전라북도':'Jeonbuk','전라남도':'Jeonnam',
            '경상북도':'Gyeongbuk','경상남도':'Gyeongnam','제주특별자치도':'Jeju',
            '제주도':'Jeju'
        }
        # Pivot
        pivot_raw = region_df.pivot_table(
            index='Year', 
            columns='지역', 
            values='Population', 
            aggfunc='sum'
        ).fillna(0).sort_index()

        # Rename columns to English
        pivot = pivot_raw.rename(columns=region_map)

        # 5) Tabs
        tabs = st.tabs(["Basic Stats", "Nationwide Trend", "Region Distribution", "Change Analysis", "Visualization"])

        # Tab 1: Basic Stats
        with tabs[0]:
            st.header("Basic Statistics")
            buf = io.StringIO()
            orig_df.info(buf=buf)
            st.text(buf.getvalue())
            st.subheader("Descriptive Statistics")
            st.dataframe(orig_df[['Population','Births','Deaths']].describe())

        # Tab 2: Nationwide Trend
        with tabs[1]:
            st.header("Nationwide Trend & Projection")
            nation = orig_df[orig_df['지역']=='전국'].sort_values('Year')
            last3 = nation.tail(3)
            avg_net = (last3['Births'] - last3['Deaths']).mean()
            ly, lp = last3['Year'].iat[-1], last3['Population'].iat[-1]
            proj_years = list(range(ly+1, 2036))
            proj_pops  = [lp + avg_net*(y-ly) for y in proj_years]
            proj_df    = pd.DataFrame({'Year': proj_years, 'Population': proj_pops})
            trend_df   = pd.concat([nation[['Year','Population']], proj_df], ignore_index=True)

            fig, ax = plt.subplots(figsize=(10,6))
            sns.lineplot(data=trend_df, x='Year', y='Population', label='Observed', ax=ax)
            sns.scatterplot(data=proj_df, x='Year', y='Population', label='Projected', ax=ax)
            ax.set_title("Population Trend by Year")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            st.pyplot(fig)

        # Tab 3: Region Distribution
        with tabs[2]:
            st.header("Population by Region (Latest Year)")
            years = pivot.index.tolist()
            if not years:
                st.warning("No regional data available.")
            else:
                latest = max(years)
                dist = pivot.loc[latest].sort_values(ascending=False)
                fig2, ax2 = plt.subplots(figsize=(10,6))
                sns.barplot(x=dist.values/1000, y=dist.index, ax=ax2, palette="tab20")
                ax2.set_title(f"Population by Region in {latest}")
                ax2.set_xlabel("Population (Thousands)")
                ax2.set_ylabel("Region")
                st.pyplot(fig2)

        # Tab 4: Change Analysis
        with tabs[3]:
            st.header("5-Year Change Analysis")
            years = sorted(pivot.index.tolist())
            if len(years) < 2:
                st.warning("Not enough data for change analysis.")
            else:
                last_year = years[-1]
                # Compare first and last year for change
                first_year = years[0]
                pop_now  = pivot.loc[last_year]
                pop_past = pivot.loc[first_year]
                change = pop_now - pop_past
                rate   = (change / pop_past) * 100
                df_change = pd.DataFrame({'Change': change, 'Rate': rate}).sort_values('Change', ascending=False)

                fig3, ax3 = plt.subplots(figsize=(8,6))
                sns.barplot(x=df_change['Change']/1000, y=df_change.index, ax=ax3, palette="Blues_d")
                ax3.set_title(f"Change from {first_year} to {last_year}")
                ax3.set_xlabel("Change (Thousands)")
                st.pyplot(fig3)

                fig4, ax4 = plt.subplots(figsize=(8,6))
                sns.barplot(x=df_change['Rate'], y=df_change.index, ax=ax4, palette="coolwarm")
                ax4.set_title(f"Change Rate from {first_year} to {last_year} (%)")
                ax4.set_xlabel("Rate (%)")
                st.pyplot(fig4)

        # Tab 5: Visualization (Cumulative Area)
        with tabs[4]:
            st.header("Cumulative Population Area Chart")
            years_arr = np.array(pivot.index.tolist(), dtype=int)
            data = [pivot[col].to_numpy(dtype=float) for col in pivot.columns]
            fig5, ax5 = plt.subplots(figsize=(12,7))
            palette = sns.color_palette("tab20", n_colors=len(data))
            cum = np.zeros_like(years_arr, dtype=float)
            for vals, color, label in zip(data, palette, pivot.columns):
                ax5.fill_between(years_arr, cum, cum + vals, label=label, color=color)
                cum += vals
            ax5.set_title("Population by Region Over Years")
            ax5.set_xlabel("Year")
            ax5.set_ylabel("Population")
            ax5.legend(title="Region", bbox_to_anchor=(1,1))
            plt.tight_layout()
            st.pyplot(fig5)
# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()