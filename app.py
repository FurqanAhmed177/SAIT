import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io

st.set_page_config(page_title="Student Attendance Tracker", page_icon="📊", layout="wide")

st.title("📊 Student Attendance Tracker")
st.markdown("Upload an Excel file to identify students with attendance below **75%**.")

# ── Sidebar: instructions ────────────────────────────────────────────────────
with st.sidebar:
    st.header("📋 How to Use")
    st.markdown("""
1. Prepare an Excel file with these columns:
   - **Student Name**
   - **Classes Held**
   - **Classes Attended**
2. Upload the file below.
3. View students below 75% attendance.
""")
    st.markdown("---")
    st.subheader("📥 Download Sample File")

    sample_data = pd.DataFrame({
        "Student Name": ["Alice Johnson", "Bob Smith", "Carol White", "David Brown",
                         "Eva Green", "Frank Lee", "Grace Kim", "Henry Park"],
        "Classes Held": [40, 40, 40, 40, 40, 40, 40, 40],
        "Classes Attended": [38, 28, 35, 20, 30, 15, 32, 25],
    })
    buf = io.BytesIO()
    sample_data.to_excel(buf, index=False)
    st.download_button("⬇️ Download Sample Excel",
                       data=buf.getvalue(),
                       file_name="sample_attendance.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ── File upload ───────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Normalise column names
        df.columns = df.columns.str.strip().str.title()

        required = {"Student Name", "Classes Held", "Classes Attended"}
        if not required.issubset(df.columns):
            st.error(f"❌ Missing columns. Required: {required}. Found: {set(df.columns)}")
            st.stop()

        df = df.dropna(subset=["Student Name", "Classes Held", "Classes Attended"])
        df["Classes Held"] = pd.to_numeric(df["Classes Held"], errors="coerce")
        df["Classes Attended"] = pd.to_numeric(df["Classes Attended"], errors="coerce")
        df = df.dropna(subset=["Classes Held", "Classes Attended"])
        df["Attendance (%)"] = (df["Classes Attended"] / df["Classes Held"] * 100).round(2)

        low = df[df["Attendance (%)"] < 75].sort_values("Attendance (%)")

        # ── Summary metrics ───────────────────────────────────────────────────
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Students", len(df))
        col2.metric("Below 75%", len(low), delta=f"{len(low)/len(df)*100:.1f}%", delta_color="inverse")
        col3.metric("Avg Attendance", f"{df['Attendance (%)'].mean():.1f}%")

        st.markdown("---")

        if low.empty:
            st.success("🎉 All students have attendance ≥ 75%!")
        else:
            tab1, tab2 = st.tabs(["📋 Table", "📊 Chart"])

            with tab1:
                st.subheader(f"Students Below 75% Attendance ({len(low)} students)")
                display_df = low[["Student Name", "Classes Held", "Classes Attended", "Attendance (%)"]].reset_index(drop=True)
                display_df.index += 1

                def color_row(val):
                    if val < 50:
                        return "background-color: #ffd6d6; color: #8b0000"
                    elif val < 65:
                        return "background-color: #ffe8cc; color: #7a4000"
                    else:
                        return "background-color: #fff9c4; color: #5a4d00"

                try:
                    styled = (display_df.style
                              .map(color_row, subset=["Attendance (%)"])
                              .format({"Attendance (%)": "{:.2f}%"}))
                except AttributeError:
                    styled = (display_df.style
                              .applymap(color_row, subset=["Attendance (%)"])
                              .format({"Attendance (%)": "{:.2f}%"}))
                st.dataframe(styled, use_container_width=True)

                buf2 = io.BytesIO()
                display_df.to_excel(buf2, index=False)
                st.download_button("⬇️ Download Filtered Results",
                                   data=buf2.getvalue(),
                                   file_name="low_attendance_students.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            with tab2:
                st.subheader("Attendance Chart — Students Below 75%")
                fig, ax = plt.subplots(figsize=(max(8, len(low) * 0.8), 6))

                colors = []
                for val in low["Attendance (%)"]:
                    if val < 50:
                        colors.append("#e74c3c")
                    elif val < 65:
                        colors.append("#e67e22")
                    else:
                        colors.append("#f1c40f")

                bars = ax.barh(low["Student Name"], low["Attendance (%)"], color=colors, edgecolor="white", height=0.6)

                # 75% threshold line
                ax.axvline(75, color="#2ecc71", linewidth=2, linestyle="--", label="75% Threshold")

                # Value labels
                for bar, val in zip(bars, low["Attendance (%)"]):
                    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                            f"{val:.1f}%", va="center", fontsize=9, fontweight="bold")

                ax.set_xlabel("Attendance (%)", fontsize=11)
                ax.set_title("Students with Attendance Below 75%", fontsize=14, fontweight="bold", pad=15)
                ax.set_xlim(0, 100)
                ax.invert_yaxis()
                ax.set_facecolor("#f9f9f9")
                fig.patch.set_facecolor("white")
                ax.spines[["top", "right"]].set_visible(False)

                legend_patches = [
                    mpatches.Patch(color="#e74c3c", label="< 50% (Critical)"),
                    mpatches.Patch(color="#e67e22", label="50–65% (Warning)"),
                    mpatches.Patch(color="#f1c40f", label="65–75% (Low)"),
                ]
                ax.legend(handles=legend_patches + [plt.Line2D([0], [0], color="#2ecc71", linewidth=2, linestyle="--", label="75% Threshold")],
                          loc="lower right", fontsize=9)

                plt.tight_layout()
                st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
else:
    st.info("👆 Upload an Excel file to get started. Download the sample file from the sidebar to try it out.")