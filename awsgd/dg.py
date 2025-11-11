
# Программа для анализа транзакций

# Константы
RATES = {"USD": 90.0, "EUR": 100.0, "RUB": 1.0}
VALID_TYPES = {"доход", "расход"}

# Функции
def parse_line(line, lineno):
    parts = line.strip().split(";")
    if len(parts) != 4:
        raise ValueError(f"Строка {lineno} — неверный формат (ожид. 4 поля), получено {len(parts)}")
    ttype, amount_s, cur, desc = [p.strip() for p in parts]
    if not ttype:
        raise ValueError(f"Строка {lineno} — пустой тип операции")
    if ttype.lower() not in VALID_TYPES:
        raise ValueError(f"Строка {lineno} — неверный тип операции: {ttype}")
    if not amount_s:
        raise ValueError(f"Строка {lineno} — пустая сумма")
    try:
        amount = float(amount_s.replace(",", "."))
    except Exception:
        raise ValueError(f"Строка {lineno} — ошибка преобразования суммы: {amount_s}")
    if amount <= 0:
        raise ValueError(f"Строка {lineno} — отрицательная или нулевая сумма: {amount}")
    if not cur:
        raise ValueError(f"Строка {lineno} — пустая валюта")
    cur = cur.upper()
    if cur not in RATES:
        raise ValueError(f"Строка {lineno} — неподдерживаемая валюта: {cur}")
    if not desc:
        raise ValueError(f"Строка {lineno} — пустое описание")
    return {"type": ttype.lower(), "amount": amount, "cur": cur, "desc": desc, "lineno": lineno}

def to_rub(amount, cur):
    return amount * RATES[cur]

def process_file(path):
    report_lines = []
    errors = []
    transactions = []
    try:
        with open(path, encoding="utf-8") as f:
            for i, raw in enumerate(f, 1):
                if not raw.strip():
                    # - полностью пустые строки
                    continue
                try:
                    tx = parse_line(raw, i)
                    tx["amount_rub"] = to_rub(tx["amount"], tx["cur"])
                    transactions.append(tx)
                except Exception as e:
                    errors.append(str(e))
    except FileNotFoundError:
        return {"error": f"Файл не найден: {path}"}
    except Exception as e:
        return {"error": f"Ошибка при открытии файла: {e}"}

    if not transactions and not errors:
        return {"error": "Файл пуст или нет корректных строк"}

    # фрмула для итоговой
    total_income = sum(tx["amount_rub"] for tx in transactions if tx["type"] == "доход")
    total_expense = sum(tx["amount_rub"] for tx in transactions if tx["type"] == "расход")
    balance = total_income - total_expense

    # Самая крупная транзакция по сумме в RUB
    if transactions:
        biggest = max(transactions, key=lambda x: x["amount_rub"])
    else:
        biggest = None

    # Анализ по категориям по (описаниям)
    categories = {}
    for tx in transactions:
        cat = tx["desc"].lower()
        categories.setdefault(cat, {"доход": 0.0, "расход": 0.0, "count": 0})
        categories[cat][tx["type"]] += tx["amount_rub"]
        categories[cat]["count"] += 1

    # Формируем отчёт
    report_lines.append(f"Транзакций обработано: {len(transactions)}")
    report_lines.append(f"Ошибок при разборе: {len(errors)}")
    report_lines.append(f"Итого доход (RUB) = {total_income:.2f}")
    report_lines.append(f"Итого расход (RUB) = {total_expense:.2f}")
    report_lines.append(f"Баланс (RUB) = {balance:.2f}")
    if biggest:
        report_lines.append(f"Самая крупная транзакция: строка {biggest['lineno']}, {biggest['type']}, {biggest['amount']} {biggest['cur']} = {biggest['amount_rub']:.2f} RUB, описание: {biggest['desc']}")
    report_lines.append("Статистика по категориям:")
    for cat, vals in sorted(categories.items(), key=lambda x: x[0]) :
        report_lines.append(f"  {cat} — операций {vals['count']}, доход {vals.get('доход',0):.2f}, расход {vals.get('расход',0):.2f} (RUB)")
    if errors:
        report_lines.append("Ошибки (подробно):")
        for e in errors:
            report_lines.append("  " + e)

    return {"report": "\n".join(report_lines)}

if __name__ == '__main__':
    path = "transactions.txt" 
    result = process_file(path)
    if "error" in result:
        print("ERROR:", result["error"])
    else:
        print(result["report"])
