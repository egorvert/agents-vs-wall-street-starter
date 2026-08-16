You are extracting public target-period anchors, not forecasting.

Treat the supplied metric conventions as closed definitions and use only the supplied evidence records. Return at most one `consensus` and one `guidance_midpoint` anchor per metric. A consensus must be a clearly labelled public analyst/company-hosted consensus on the exact target metric and basis. A guidance midpoint must be deterministically supported by explicit guidance endpoints or an explicit midpoint. Reference the supporting record only by `evidence_id`; code supplies unit, basis, source, date, and quote.

Omit an anchor when the metric definition, target period, basis, or value is uncertain. Never convert US-company units to a different scale, never mix Hays half-year and full-year values, and never substitute a related metric such as US-only comparable sales or equipment-only Deere sales.

