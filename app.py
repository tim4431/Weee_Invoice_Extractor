import streamlit as st
import re
from bs4 import BeautifulSoup

# -------------------------
# Functions to extract invoice details
# -------------------------


def extract_items_from_invoice(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []

    # Find the container holding the product details.
    items_container = soup.find("div", class_="detail_itemsInfo__za_PG")
    if not items_container:
        st.error("Items container not found.")
        return items

    # Each product appears in a block with a class containing "py-400".
    product_divs = items_container.find_all("div", class_=lambda c: c and "py-400" in c)

    for product in product_divs:
        # Extract product name from a div whose class contains "enki-body-xs-medium".
        name_div = product.find(
            "div", class_=lambda c: c and "enki-body-xs-medium" in c
        )
        product_name = name_div.get_text(strip=True) if name_div else "N/A"

        # Extract unit price and quantity from spans that include "单价" and "数量".
        spans = product.find_all("span", class_=lambda c: c and "enki-body-xs" in c)
        unit_price = None
        quantity = None
        for span in spans:
            text = span.get_text(strip=True)
            if "单价" in text:
                match = re.search(r"单价[:：]\s*\$?([\d\.]+)", text)
                if match:
                    unit_price = match.group(1)
            elif "数量" in text:
                match = re.search(r"数量[:：]\s*(\d+)", text)
                if match:
                    quantity = match.group(1)

        # The line total is found in a div with a class containing "enki-body-sm-medium".
        total_div = product.find(
            "div", class_=lambda c: c and "enki-body-sm-medium" in c
        )
        line_total = total_div.get_text(strip=True) if total_div else "N/A"

        items.append(
            {
                "name": product_name,
                "unit_price": unit_price,
                "quantity": quantity,
                "total": line_total,
            }
        )
    return items


def extract_order_summary(html):
    soup = BeautifulSoup(html, "html.parser")
    summary = {}
    # The order summary information is in a container with classes "pt-300 px-0"
    summary_container = soup.find("div", class_="pt-300 px-0")
    if not summary_container:
        st.error("Order summary container not found.")
        return summary

    # Find each summary row; rows are typically divs with a "box-border" class.
    rows = summary_container.find_all("div", class_=lambda c: c and "box-border" in c)
    for row in rows:
        spans = row.find_all("span")
        if len(spans) >= 2:
            label = spans[0].get_text(strip=True)
            value = spans[1].get_text(strip=True)
            if "服务费" in label:
                summary["服务费"] = value
            elif "配送费" in label:
                summary["配送费"] = value
            elif "小费" in label:
                summary["小费"] = value
            elif "合计" in label:
                summary["合计"] = value
            elif "税" in label:
                summary["税"] = value
            elif "支付总额" in label:
                summary["支付总额"] = value
    return summary


# -------------------------
# Streamlit App
# -------------------------

st.title("Invoice Split Calculator")

st.markdown(
    """
    Upload your invoice HTML file. The app will display each item with a checkbox:

    - **Checked:** You pay 50% and your roommate pays 50%.
    - **Unchecked:** You pay 100%, roommate pays 0%.
    """
)

uploaded_file = st.file_uploader("Upload invoice HTML file", type=["html"])
if uploaded_file:
    html_content = uploaded_file.read().decode("utf-8")
    items = extract_items_from_invoice(html_content)
    summary = extract_order_summary(html_content)

    if not items:
        st.error("No items found in the invoice.")
    else:
        st.subheader("Invoice Items")

        # Initialize the split state for each item in session_state (if not already)
        if "item_split" not in st.session_state:
            # Default state for each item is 50 (representing a 50% split for roommate)
            st.session_state.item_split = {i: True for i in range(len(items))}

        # # 添加自定义 CSS 样式
        # st.markdown(
        #     """
        #     <style>
        #     .item-container {
        #         border: 1px solid #ddd;
        #         padding: 10px;
        #         margin-bottom: 10px;
        #         border-radius: 8px;
        #         background-color: #f9f9f9;
        #         box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        #     }
        #     .item-header {
        #         font-weight: bold;
        #         color: #333;
        #         margin-bottom: 5px;
        #     }
        #     .item-detail {
        #         color: #666;
        #         margin-bottom: 5px;
        #     }
        #     </style>
        #     """,
        #     unsafe_allow_html=True,
        # )
        # Display each item with its details and a checkbox for the split state.
        for i, item in enumerate(items):
            with st.container(border=True):
                # st.markdown('<div class="item-container">', unsafe_allow_html=True)
                # st.markdown(
                #     f'<div class="item-header">{item["name"]}</div>',
                #     unsafe_allow_html=True,
                # )

                cols = st.columns([2, 1, 1, 1, 1])
                cols[0].markdown(f"**{item['name']}**")
                cols[1].write(f"Unit Price: {item['unit_price']}")
                cols[2].write(f"Quantity: {item['quantity']}")
                cols[3].write(f"Total: {item['total']}")

                # Use a checkbox to represent the split state
                is_checked = st.session_state.item_split[i]
                new_state = cols[4].checkbox(
                    "50% Split", value=is_checked, key=f"chk_{i}"
                )

                # Update the session state based on the checkbox
                st.session_state.item_split[i] = new_state
                # st.markdown("</div>", unsafe_allow_html=True)
            # st.divider()

        st.subheader("Summary")

        if summary:
            for key, value in summary.items():
                st.write(f"{key}: {value}")

        #
        sum_total = 0.0
        yucheng_total = 0.0
        for i, item in enumerate(items):
            try:
                cost_str = item["total"].replace("$", "").replace(",", "")
                cost = float(cost_str)
            except Exception as e:
                cost = 0.0
                st.error(f"Error parsing cost for {item['name']}: {e}")

            sum_total += cost
            fraction = 0.5 if st.session_state.item_split[i] else 0.0
            yucheng_total += fraction * cost
        # calculate the portion
        portion = yucheng_total / sum_total
        st.success(f"Yucheng's portion: {portion*100:.2f}%")
        paid_total = float(summary["支付总额"].replace("$", "").replace(",", ""))
        total_owed = float(paid_total) * portion
        st.success(f"Total amount your roommate owes you: ${total_owed:.2f}")
