# Innovation Capabilities Outlook 2026 Datasets

## What's in this folder?
**Dataset Name**: Innovation Capabilities Outlook 2026  
**What it contains**: Innovation activity, capabilities, and complexity data across different fields, places, and time periods  
**Last updated**: 2026/06/04  
**Files**: 10 parquet files covering all aspects of innovation analysis

## What this data shows
This dataset tracks innovation around the world in multiple ways:
1. **Innovation Outputs**: How much innovation is happening (patents, papers, exports, trademarks)
2. **Innovation Capabilities**: Which places are strong or specialized in each field
3. **Field-Place Relationships**: How connected different innovation fields are to places
4. **Innovation Potential**: Expected innovation based on related capabilities
5. **Place Sophistication**: How complex each place's innovation ecosystem is
6. **Field Sophistication**: How complex and competitive each innovation field is
7. **Place-Place Relationships**: How similar different places are between them
8. **Field-Field Relationships**: How similar different fields are between them
9. **Reference Information**: Names and details for places and fields

---

## Main Analysis Files

### File 1: `outputs.parquet` - Innovation Activity
*The foundation dataset*

| Column Name | What it shows | Example |
|-------------|---------------|---------|
| **Period** | The year | 2020, 2021, 2022 |
| **Unit** | Location/country/region | USA, Germany, Japan |
| **Field ID** | Innovation field | T - 001, S - 045, P - 123 |
| **Outputs** | Number of innovation outputs | 1,250 patents, 500 papers |
| **Outputs (Fractional)** | Adjusted count when outputs span multiple fields/places | 0.33 (if shared across 3 fields) |
| **Population** | Population of the unit | 39,500,000 |

### File 2: `capabilites.parquet` - Innovation Capabilities

| Column Name | What it shows | Values | Meaning |
|-------------|---------------|--------|---------|
| **Innovation Capability (Normalized)** | How capable is this place in this field? | Range [0,1] | Normalized innovation presence |
| **Innovation Capability (Binary)** | Does this place have capability in this field? | True = Yes, False = No | Basic innovation presence |
| **Absolute Capability (Binary)** | Is this place a top global producer? | True = Yes, False = No | Global leadership |
| **Relative Capability (Binary)** | Is this field a specialty for them, given what they do in other fields? | True = Yes, False = No | Local specialization |

### File 3: `dens.parquet` - Field Relationships

| Column Name | What it shows | Example | Meaning |
|-------------|---------------|---------|---------|
| **Relatedness Density** | How connected is this field to other fields the place already masters? | 0.75 | 75% of related fields are already mastered |

### File 4: `potentials.parquet` - Growth Potential

| Column Name | What it shows | Example | Meaning |
|-------------|---------------|---------|---------|
| **Potential** | Expected number of outputs based on capabilities in related fields | 150 | Expected to produce ~150 outputs in this field |

---

## Complexity Analysis Files

### File 5: `unit_complexities.parquet` - Place Sophistication
*Index: Period + Unit (no Field ID - this is about places overall)*

| Column Name | What it shows | Example | Meaning |
|-------------|---------------|---------|---------|
| **Diversity Share** | Fraction of innovation fields the place has mastered | 0.45 | Masters 45% of all innovation fields |
| **Ecosystem Complexity Index** | How sophisticated is their innovation ecosystem? | 1.8 | High complexity innovation ecosystem |
| **Complexity Outlook Index** | How well-positioned is this place to move into complex fields? | 0.75 | Well-positioned to diversify into complex fields |
| **Growth Outlook Index** | How well-positioned is this place to move into fast-growing fields? | 0.82 | Well-positioned to diversify into fast-growing fields |

**Understanding the outlooks**:
- **High Complexity Outlook Index** = This place has the right foundation to easily develop capabilities in sophisticated, complex innovation fields
- **High Growth Outlook Index** = This place has the right foundation to easily develop capabilities in rapidly expanding innovation fields

### File 6: `field_complexities.parquet` - Field Sophistication
*Index: Period + Field ID (no Unit - this is about fields overall)*

| Column Name | What it shows | Example | Meaning |
|-------------|---------------|---------|---------|
| **Ubiquity Share** | Fraction of places that have mastered this field | 0.12 | Only 12% of places master this field |
| **Capability Complexity Index** | How complex/difficult is this innovation field? | 2.3 | Very complex field to master |
| **Complexity Outlook Index** | How easy is it for complex places to enter this field? | 0.85 | Complex places can easily enter this field |
| **Growth Outlook Index** | How easy is it for fast-growing places to enter this field? | 0.65 | Fast-growing places can relatively easily enter this field |

**Understanding the field outlooks**:
- **High Complexity Outlook Index** = Sophisticated places with complex innovation ecosystems can easily diversify into this field
- **High Growth Outlook Index** = Places with fast-growing innovation ecosystems can easily diversify into this field

**What this tells us**: 
- **Low Ubiquity Share** = Rare, often difficult field (few places can do it)
- **High Complexity Index** = Sophisticated field requiring advanced capabilities
- **High Complexity Outlook** = Field is accessible to complex innovation ecosystems
- **High Growth Outlook** = Field is accessible to rapidly growing innovation ecosystems


## Proximity Analysis Files

### File 7: `unit_proximities.parquet` - Place Similarities
*Index: Period + Unit 1 + Unit 2*

| Column Name | What it shows | Example | Meaning |
|-------------|---------------|---------|---------|
| **Proximity** | Probability of both locations to share a capability | 0.20 | These places share ~20% of their capabilities |

Notes: Public dataset contains latest period only to make the file size manageable. Unit pairs are not mirrored for the same reason.

### File 8: `field_proximities.parquet` - Field Similarities
*Index: Period + Field ID 1 + Field ID 2*

| Column Name | What it shows | Example | Meaning |
|-------------|---------------|---------|---------|
| **Proximity** | Probability of both fields to appear in the same location | 0.50 | These capabilities appear together 50% of the time |

Notes: Public dataset contains latest period only to make the file size manageable. Field pairs are not mirrored for the same reason.

---

## Reference/Lookup Files

### File 9: `fields.parquet` - Field Information
*Index: Field ID*

| Column Name | What it shows | Example |
|-------------|---------------|---------|
| **Field Name** | Human-readable name of the innovation field | "Artificial Intelligence" |
| **Domain ID** | Which broader domain this field belongs to | T - D3 |
| **Domain Name** | Name of the broader domain | "Information Technology" |
| **Dimension Name** | Which type of innovation this represents | "Technology" |

**Innovation dimensions**:
- **Technology** → Measured by patents
- **Science** → Measured by scientific publications  
- **Production** → Measured by exports
- **Entrepreneurship** → Measured by trademarks

### File 10: `units.parquet` - Place Information
*Index: Period + Unit*

| Column Name | What it shows | Example |
|-------------|---------------|---------|
| **Unit Name** | Full name of the place | "United States" |
| **Continent** | Geographic region | "North America" |
| **Income Group** | World Bank income classification | "High Income" |
| **GDP PPP** | GDP in purchasing power parity (billions USD) | 21,400 |
| **Population** | Population count | 331,000,000 |
| **GDP PC** | GDP per capita | 65,000 |