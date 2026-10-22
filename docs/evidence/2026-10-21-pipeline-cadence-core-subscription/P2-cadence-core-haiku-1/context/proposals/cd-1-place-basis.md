---
decision_id: cd-1-place-basis
status: proposed
question: Which place (state and county) is used for an award, and where do rows with no state or county go?
choice: Place of performance (primary_place_of_performance state and county codes). Rows with no state or county go to an UNKNOWN member in dim_place, so county totals and state totals still reconcile to the source total. Connecticut planning-region county codes (state 09, county 09110 to 09190) also map to the state's UNKNOWN county, with the code kept in source_county_fips5. No crosswalk is used, because none is in data/raw/ (plan update cycle 4, MF-10). A place with a missing state maps the state key to UNKNOWN too. Places in the territory states 60, 66, 69, 72 and 78, which have no county rows in the census files, keep their state and map to the state's UNKNOWN county with no population join (plan update cycle 5, MF-11).
rationale: Place of performance is where the money is spent, which is the question analysts ask by state and county. Excluding unplaced rows would make check 4 fail against the source total. The option rejected is the recipient location, which tells where the recipient is registered and not where the money goes.
---
Ticket: cd-1
