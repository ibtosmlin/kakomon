# モジュールの読み込み
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

cwd = Path(__file__).parent
data = cwd / "analysis_data"
subjects = ["算数", "国語", "理科", "社会"]
cols = [
    "KEY",
    "科目",
    "学校",
    "年度",
    "試験",
    "大分野",
    "中分野",
    "分野",
    "出題数",
]
tablecsvname = "table.csv"
schoollist = "school.csv"


def create_keys(subject: str) -> pd.DataFrame | None:
    seg_0 = data / f"{subject}_seg_0.csv"
    seg_1 = data / f"{subject}_seg_1.csv"
    seg_2 = data / f"{subject}_seg_2.csv"
    if seg_0.exists() and seg_1.exists() and seg_2.exists():
        df0 = pd.read_csv(seg_0)
        df1 = pd.read_csv(seg_1)
        df2 = pd.read_csv(seg_2)
        df = df2.merge(df1, on="中分野")
        df = df.merge(df0, on="大分野")
        df["KEY"] = (
            df["大分野NUM"].astype(str).str.zfill(3)
            + df["中分野NUM"].astype(str).str.zfill(3)
            + df["分野NUM"].astype(str).str.zfill(3)
        )
        df["KEY"] = df["KEY"] + "K"
        return df
    else:
        print(f"❌:create_keys skip {subject}")


def read_data(subject):
    dfs = []
    for file in data.glob(f"{subject}_*.csv"):
        if not file.name.startswith(f"{subject}_seg_"):
            school: str = file.stem.split("_")[-1]
            df = pd.read_csv(file)
            df["学校"] = school
            df["出題数"] = 1
            dfs.append(df)
    df = pd.concat(dfs, axis=0)
    return df


def data_merge(df, df_key):
    ndf = df.merge(df_key, on="分野")
    dummy = df[["学校", "年度", "試験"]]
    dummy = dummy.drop_duplicates()
    dummy = dummy.merge(df_key, how="cross")
    dummy["出題数"] = 0
    ndf = pd.concat([ndf, dummy])
    return ndf


def update_csv():
    dfs = []
    for subject in subjects:
        df_keys = create_keys(subject)
        if df_keys is None:
            continue
        df = read_data(subject)
        if df is None:
            continue
        df = data_merge(df, df_keys)
        df["科目"] = subject
        df = df[cols]
        dfs.append(df)
    df = pd.concat(dfs)
    df.to_csv(data / tablecsvname, index=False)


def should_update_table_csv(folder_path: Path, target_filename: str) -> bool:
    today = datetime.today().date()
    target_file = folder_path / target_filename

    if not target_file.exists():
        print(f"❌{target_filename} が存在しません")
        return True

    target_mtime = datetime.fromtimestamp(target_file.stat().st_mtime)

    # 条件①: 今日でない
    if target_mtime.date() != today:
        return True

    # 条件②: 他のCSVファイルより古い
    for csv_file in folder_path.glob("*.csv"):
        if csv_file.name == target_filename:
            continue
        other_mtime = datetime.fromtimestamp(csv_file.stat().st_mtime)
        if other_mtime > target_mtime:
            return True

    return False


def read_csv():
    if should_update_table_csv(data, tablecsvname):
        update_csv()
        print(f"✅{tablecsvname}を更新しました")
    df = pd.read_csv(
        data / tablecsvname,
        index_col=None,
    )
    return df


subjects = ["算数", "国語", "理科", "社会"]
cols = [
    "KEY",
    "科目",
    "学校",
    "年度",
    "試験",
    "大分野",
    "中分野",
    "分野",
    "出題数",
]

st.set_page_config(page_title="出題傾向分析", layout="wide")


def main():
    st.title("出題傾向分析")

    df = read_csv()
    df_school = df["学校"].dropna().drop_duplicates().tolist()
    default_schools = ["芝中学"]

    col1, col2 = st.columns(2)
    with col1:
        subject = st.selectbox("教科を選択してください", subjects)
    with col2:
        schools = st.multiselect(
            "学校を選択してください",
            df_school,
            default=default_schools,
        )

    base_df = df[(df["科目"] == subject) & (df["学校"].isin(schools))]

    st.write("---")
    col1, col2, col3 = st.columns(3)

    filtered_df = None
    display_mode = "出題数"
    if not base_df.empty:
        years = [int(year) for year in sorted(base_df["年度"].dropna().unique())]
        max_year = years[-1]

        with col1:
            start_year: int = st.selectbox("開始年度を選択", years, index=0)

        with col2:
            exams = st.multiselect(
                "試験を選択してください（任意）",
                sorted(base_df["試験"].dropna().drop_duplicates()),
            )

        with col3:
            display_mode = st.radio(
                "表示モードを選択",
                ["出題数", "パーセント"],
                horizontal=True,
            )

        filtered_df = base_df[
            (base_df["年度"] >= start_year) & (base_df["年度"] <= max_year)
        ]
        if exams:
            filtered_df = filtered_df[filtered_df["試験"].isin(exams)]

        st.subheader(f"{start_year}年度〜{max_year}年度のデータ")

    else:
        st.warning("選択された条件に該当するデータがありません")

    if filtered_df is not None:
        show_chart_0(filtered_df=filtered_df, schools=schools, display_mode=display_mode)
        show_chart_1(
            filtered_df=filtered_df, schools=schools, display_mode=display_mode
        )


def show_chart_0(
    filtered_df: pd.DataFrame,
    schools: list[str],
    display_mode: str,
) -> None:
    if filtered_df is None or len(schools) == 0:
        st.warning("学校を1校以上選択してください")
        return

    # X軸の最大値を算出
    if display_mode == "パーセント":
        xaxis_range = [0, 25]
    else:
        max_value = (
            filtered_df.groupby(["学校", "分野"])["出題数"]
            .sum()
            .groupby("分野")
            .sum()
            .max()
        )
        xaxis_range = [0, max_value * 1.1]

    plot_stacked_chart(
        filtered_df=filtered_df,
        container=st,
        chart_key="stacked_chart_all",
        display_mode=display_mode,
        xaxis_range=xaxis_range,
        schools=schools,
    )


def show_chart_1(
    filtered_df: pd.DataFrame, schools: list[str], display_mode: str
) -> None:
    school_count = len(schools)
    if filtered_df is None:
        return
    if school_count == 0:
        st.warning("学校を1校以上選択してください")
        return

    elif school_count == 1:
        st.subheader(f"●{schools[0]} の分野別出題数")
        plot_chart_1(
            filtered_df,
            schools[0],
            st,
            chart_key=f"chart_{schools[0]}",
            display_mode=display_mode,
        )

    else:
        col1, col2 = st.columns(2)
        for hi in range((school_count + 1) // 2):
            if hi * 2 < school_count:
                plot_chart_1(
                    filtered_df,
                    schools[hi * 2],
                    col1,
                    chart_key=f"chart_{schools[hi * 2]}",
                    display_mode=display_mode,
                )
            if hi * 2 + 1 < school_count:
                plot_chart_1(
                    filtered_df,
                    schools[hi * 2 + 1],
                    col2,
                    chart_key=f"chart_{schools[hi * 2 + 1]}",
                    display_mode=display_mode,
                )
        st.write("---")


def plot_stacked_chart(
    filtered_df: pd.DataFrame,
    container,
    chart_key: str,
    display_mode: str,
    xaxis_range: list[float],
    schools:list[str]
) -> None:
    summary_df = (
        filtered_df.groupby(["学校", "分野", "中分野", "KEY"])["出題数"]
        .sum()
        .reset_index()
    )

    # パーセント表示に変換
    if display_mode == "パーセント":
        total_by_school = summary_df.groupby("学校")["出題数"].transform("sum")
        summary_df["出題数"] = (summary_df["出題数"] / total_by_school * 100).round(1)
        x_title = "出題割合（%）"
        text_format = "%{text:.1f}%"
    else:
        x_title = "出題数"
        text_format = "%{text}"

    # ダミー行の生成
    dummy_rows = []
    for middle in summary_df["中分野"].dropna().unique():
        sub_df = summary_df[summary_df["中分野"] == middle]
        min_key = sub_df["KEY"].min()[:6]
        dummy_rows.append(
            {
                "学校": "",
                "分野": "",
                "中分野": middle,
                "KEY": min_key,
                "出題数": 0,
                "表示ラベル": (f"【{middle}】" + "—" * 20)[:20],
            }
        )
    summary_df["表示ラベル"] = summary_df["分野"]
    combined_df = pd.concat([pd.DataFrame(dummy_rows), summary_df], ignore_index=True)
    combined_df = combined_df.sort_values("KEY", ascending=False)
    key_df = (combined_df[["表示ラベル", "KEY"]].drop_duplicates())["表示ラベル"]

    fig = px.bar(
        combined_df,
        x="出題数",
        y="表示ラベル",
        color="学校",
        orientation="h",
        title="分野別出題傾向（学校別積み上げ）",
        text="出題数",
        category_orders={"学校": schools},
    )

    fig.update_traces(texttemplate=text_format)
    height = max(600, 30 * len(combined_df)) // len(schools)
    fig.update_layout(
        xaxis=dict(range=xaxis_range),
        yaxis_title="分野",
        xaxis_title=x_title,
        height=height,
        margin=dict(l=200),
        yaxis=dict(
            automargin=True,
            tickfont=dict(size=12, color="black"),
            categoryorder="array",
            categoryarray=key_df,
        ),
    )

    container.plotly_chart(fig, use_container_width=True, key=chart_key)


def plot_chart_1(
    filtered_df: pd.DataFrame,
    school: str,
    container,
    chart_key: str,
    display_mode: str,
) -> None:
    school_df = filtered_df[filtered_df["学校"] == school]

    summary_df = (
        school_df.groupby(["分野", "中分野", "KEY"])["出題数"].sum().reset_index()
    )

    # パーセント表示に変換
    if display_mode == "パーセント":
        total = summary_df["出題数"].sum()
        summary_df["出題数"] = (summary_df["出題数"] / total * 100).round(1)
        x_title = "出題割合（%）"
        text_format = "%{text:.1f}%"
    else:
        x_title = "出題数"
        text_format = "%{text}"

    # X軸の最大値を取得（出題数 or パーセント）

    if display_mode == "パーセント":
        xaxis_range = [0, 25]
    else:
        xaxis_range = [0, 40]

    # ダミー行の生成
    dummy_rows = []
    for middle in summary_df["中分野"].dropna().unique():
        sub_df = summary_df[summary_df["中分野"] == middle]
        min_key = sub_df["KEY"].min()[:6]
        dummy_rows.append(
            {
                "分野": "",
                "中分野": middle,
                "KEY": min_key,
                "出題数": 0,
                "表示ラベル": (f"【{middle}】" + "—" * 20)[:20],
            }
        )

    summary_df["表示ラベル"] = summary_df["分野"]
    combined_df = pd.concat([pd.DataFrame(dummy_rows), summary_df], ignore_index=True)
    combined_df = combined_df.sort_values("KEY", ascending=False)

    fig = px.bar(
        combined_df,
        x="出題数",
        y="表示ラベル",
        orientation="h",
        title=f"{school} の分野別出題傾向",
        text="出題数",
    )

    fig.update_traces(texttemplate=text_format)
    height = max(600, 30 * len(combined_df))
    fig.update_layout(
        xaxis=dict(range=xaxis_range),
        yaxis_title="分野",
        xaxis_title=x_title,
        height=height,
        margin=dict(l=200),
        yaxis=dict(
            automargin=True,
            tickfont=dict(size=12, color="black"),
        ),
    )

    container.plotly_chart(fig, use_container_width=True, key=chart_key)


if __name__ == "__main__":
    main()
