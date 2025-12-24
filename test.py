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
            "学校を選択してください（最大2校）",
            df_school,
            default=default_schools,
            max_selections=2,
        )

    base_df = df[(df["科目"] == subject) & (df["学校"].isin(schools))]

    st.write("---")
    col1, col2 = st.columns(2)

    filtered_df = None
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

        filtered_df = base_df[
            (base_df["年度"] >= start_year) & (base_df["年度"] <= max_year)
        ]
        if exams:
            filtered_df = filtered_df[filtered_df["試験"].isin(exams)]

        st.subheader(f"{start_year}年度〜{max_year}年度のデータ")
        # st.dataframe(filtered_df)

    else:
        st.warning("選択された条件に該当するデータがありません")

    if filtered_df is not None:
        show_chart_1(filtered_df=filtered_df, schools=schools)


def show_chart_1(filtered_df: pd.DataFrame, schools: list[str]) -> None:
    if filtered_df is None:
        return
    if len(schools) == 0:
        st.warning("学校を1校以上選択してください")
        return

    elif len(schools) == 1:
        st.subheader(f"{schools[0]} の分野別出題数")
        plot_chart_1(filtered_df, schools[0], st, chart_key=f"chart_{schools[0]}")

    elif len(schools) == 2:
        col1, col2 = st.columns(2)
        plot_chart_1(filtered_df, schools[0], col1, chart_key=f"chart_{schools[0]}")
        plot_chart_1(filtered_df, schools[1], col2, chart_key=f"chart_{schools[1]}")

    else:
        st.warning("比較表示は最大2校までです")


def plot_chart_1(
    filtered_df: pd.DataFrame, school: str, container, chart_key: str
) -> None:
    school_df = filtered_df[filtered_df["学校"] == school]

    # 分野ごとに出題数を集計し、KEYと中分野を保持
    summary_df = (
        school_df.groupby(["分野", "中分野", "KEY"])["出題数"].sum().reset_index()
    )

    # KEYを数値化した列を追加（並び順制御用）
    summary_df["KEY_INT"] = summary_df["KEY"].astype(int)

    # 中分野見出し用のダミー行を作成（KEY_INTをその中分野の最小より小さく）
    dummy_rows = []
    for middle in summary_df["中分野"].dropna().unique():
        sub_df = summary_df[summary_df["中分野"] == middle]
        min_key_int = sub_df["KEY_INT"].min()
        dummy_rows.append(
            {
                "分野": "",
                "中分野": middle,
                "KEY": str(min_key_int - 1).zfill(9),  # KEYは文字列として保持
                "KEY_INT": min_key_int - 1,
                "出題数": 0,
                "表示ラベル": (f"【{middle}】" + "—" * 20)[:20],
            }
        )

    # 通常ラベルを生成
    summary_df["表示ラベル"] = summary_df["分野"]

    # ダミー行と統合して KEY_INT で並び替え
    combined_df = pd.concat([pd.DataFrame(dummy_rows), summary_df], ignore_index=True)
    combined_df = combined_df.sort_values("KEY_INT", ascending=False)

    # グラフ生成
    fig = px.bar(
        combined_df,
        x="出題数",
        y="表示ラベル",
        orientation="h",
        title=f"{school} の分野別出題数",
        text="出題数",
    )

    # 高さ調整（1ラベルあたり30px）
    height = max(600, 30 * len(combined_df))
    fig.update_layout(
        yaxis_title="分野",
        xaxis_title="出題数",
        height=height,
        margin=dict(l=200),
        yaxis=dict(
            automargin=True,
            tickmode="linear",
            tickfont=dict(size=10),
        ),
    )

    container.plotly_chart(fig, use_container_width=True, key=chart_key)


if __name__ == "__main__":
    main()
