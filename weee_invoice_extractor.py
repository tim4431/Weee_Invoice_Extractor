import re
from bs4 import BeautifulSoup


def extract_items_from_invoice(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []

    # Find the container holding the product details.
    items_container = soup.find("div", class_="detail_itemsInfo__za_PG")
    if not items_container:
        print("Items container not found.")
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
        print("Order summary container not found.")
        return summary

    # Find each summary row; rows are typically divs with a "box-border" class.
    rows = summary_container.find_all("div", class_=lambda c: c and "box-border" in c)
    for row in rows:
        spans = row.find_all("span")
        if len(spans) >= 2:
            # The first span usually contains the label; note that in some cases it may include extra text like "免费".
            label = spans[0].get_text(strip=True)
            # The second span contains the monetary value.
            value = spans[1].get_text(strip=True)
            # Match against the desired fields.
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


if __name__ == "__main__":
    # Replace 'invoice.html' with the path to your HTML file
    with open("invoice.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    print("Extracted Product Items:")
    items = extract_items_from_invoice(html_content)
    for item in items:
        print("Name:", item["name"])
        print("Unit Price:", item["unit_price"])
        print("Quantity:", item["quantity"])
        print("Total:", item["total"])
        print("-" * 40)

    print("\nExtracted Order Summary:")
    summary = extract_order_summary(html_content)
    for key, value in summary.items():
        print(f"{key}: {value}")
