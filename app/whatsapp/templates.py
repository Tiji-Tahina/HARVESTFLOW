def text_msg(text: str) -> dict:
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "type": "text",
        "text": {"body": text},
    }


def list_msg(header: str, body: str, footer: str, sections: list[dict]) -> dict:
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "footer": {"text": footer},
            "action": {"button": "Options", "sections": sections},
        },
    }


def button_msg(body: str, buttons: list[dict]) -> dict:
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {"buttons": buttons},
        },
    }


def product_sections(products: list[dict], max_items: int = 10) -> list[dict]:
    rows = []
    for i, p in enumerate(products[:max_items]):
        rows.append(
            {
                "id": f"prod_{p['id']}",
                "title": f"{p['name']} ({p['unit_of_measure']})",
                "description": p["category"],
            }
        )
    return [{"title": "Available Products", "rows": rows}]


def menu_sections(options: list[tuple[str, str]]) -> list[dict]:
    return [
        {
            "title": "Menu",
            "rows": [
                {"id": f"opt_{i}", "title": title, "description": desc}
                for i, (title, desc) in enumerate(options, 1)
            ],
        }
    ]


def confirm_buttons() -> dict:
    return button_msg(
        "Submit this harvest data?",
        [
            {"type": "reply", "reply": {"id": "confirm_yes", "title": "Yes, Submit"}},
            {"type": "reply", "reply": {"id": "confirm_no", "title": "No, Edit"}},
        ],
    )


def yes_no_buttons(prompt: str) -> dict:
    return button_msg(
        prompt,
        [
            {"type": "reply", "reply": {"id": "yes", "title": "Yes"}},
            {"type": "reply", "reply": {"id": "no", "title": "No"}},
        ],
    )


def harvest_summary(product: str, quantity: float, price: float, date: str, location: str) -> dict:
    return text_msg(
        f"Harvest Summary:\n\n"
        f"Product: {product}\n"
        f"Quantity: {quantity}\n"
        f"Price per unit: ${price:.2f}\n"
        f"Harvest Date: {date}\n"
        f"Location: {location}\n\n"
        f"Reply Yes to submit or No to edit."
    )
