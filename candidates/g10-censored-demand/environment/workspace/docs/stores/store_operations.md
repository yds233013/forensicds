# Store operations (extract)

- **Trading hours:** store trading hours for every date are in `store_calendar`, which is authoritative. Standard
  hours are set per region and can change; holiday hours and closures (refits) are recorded per store and date.
  Nothing is sold outside trading hours.
- **Shopper traffic:** follows a regular pattern by day type (weekday, Saturday, Sunday), measured by the door counters.
  - The shape differs between regions. In the current region, weekday traffic builds through the day and peaks in the
    evening, Saturday peaks around midday, and Sunday is concentrated in its shorter trading window.
  - How busy a day is does not change its shape: a busy weekday has the same hour-by-hour pattern as a quiet one.
- **Empty shelves:**
  - Shelf stock is the on-hand quantity; there is no backroom stock (deliveries go straight to shelf).
  - When an item is out, shoppers who wanted it leave without it.
  - The 2025 loyalty-card study found no measurable same-day return visits for the missing item and no measurable
    switching into other items in the category.
- **Stock records:** the perpetual inventory is reconciled nightly against a closing count. There is no known phantom
  stock in the extract.
