# Data on SARS-CoV-2 variants by _Our World in Data_
> For more general information on our COVID-19 data, see our main README file in [`/public/data`](https://github.com/owid/covid-19-data/tree/master/public/data).

Enabled by data from <a href="https://gisaid.org"><img src="https://www.gisaid.org/fileadmin/gisaid/img/schild.png"
width="50"/></a>. 

The data is sourced from [GISAID](https://gisaid.org), via [CoVariants](https://CoVariants.org), and we make it available as a [CSV
💾](covid-variants.csv).


### Fields

| Column field        | Description                                                                  |
|---------------------|------------------------------------------------------------------------------|
| `location`            | Name of the country (or region within a country).                            |
| `date`                | Date of the observation.                                                     |
| `variant`             | Variant name. We use the [WHO label](https://www.who.int/en/activities/tracking-SARS-CoV-2-variants/#Naming-SARS-CoV-2-variants) for Variants of Concern (VoC) and Variants of Interest (VoI), and Pango Lineage for the others. Details on variants included can be found [here](https://covariants.org/variants). |
| `num_sequences`       | Number of sequenced samples that fall into the category `variant`. |
| `perc_sequences`      | Percentage of the sequenced samples that fall into the category `variant`. |
| `num_sequences_total` | Total number of samples sequenced in the last two weeks. |

#### Special `variant` values

- `others`: All variants/mutations other than the ones specified (i.e. not listed [in this table](https://covariants.org/variants)).
- `non_who`: All variants/mutations without WHO label.

Note that `non_who` inclues `others` and other variants.

### Example
|location |date      |variant       |num_sequences|perc_sequences|num_sequences_total|
|---------|----------|--------------|-------------|--------------|-------------------|
|United Kingdom|2021-03-08|B.1.160       |4.0 |0.01 |29598|
|United Kingdom|2021-03-08|B.1.258       |17.0|0.06 |29598|
|United Kingdom|2021-03-08|B.1.221       |3.0 |0.01 |29598|
|United Kingdom|2021-03-08|B.1.1.302     |0.0 |0.0  |29598|
|United Kingdom|2021-03-08|B.1.1.277     |0.0 |0.0  |29598|
|United Kingdom|2021-03-08|B.1.367       |0.0 |0.0  |29598|
|United Kingdom|2021-03-08|B.1.177       |347.0|1.17 |29598|
|United Kingdom|2021-03-08|Beta          |60.0|0.2  |29598|
|United Kingdom|2021-03-08|Alpha         |28772.0|97.21|29598|
|United Kingdom|2021-03-08|Gamma         |6.0 |0.02 |29598|
|United Kingdom|2021-03-08|Delta         |0.0 |0.0  |29598|
|United Kingdom|2021-03-08|Kappa         |12.0|0.04 |29598|
|United Kingdom|2021-03-08|Epsilon       |3.0 |0.01 |29598|
|United Kingdom|2021-03-08|Eta           |97.0|0.33 |29598|
|United Kingdom|2021-03-08|Iota          |1.0 |0.0  |29598|
|United Kingdom|2021-03-08|S:677H.Robin1 |0.0 |0.0  |29598|
|United Kingdom|2021-03-08|S:677P.Pelican|0.0 |0.0  |29598|
|United Kingdom|2021-03-08|others        |276.0|0.93 |29598|
|United Kingdom|2021-03-08|non_who       |647.0|2.19 |29598|

In this extract, we have that during the two weeks prior to 2021-03-08, in the UK, a total of 29598 samples were
sequenced. From these, 28,772 correspond to Alpha variant and 647 are variants without WHO label.


## License

All visualizations, data, and code produced by _Our World in Data_ are completely open access under the [Creative Commons BY license](https://creativecommons.org/licenses/by/4.0/). You have the permission to use, distribute, and reproduce these in any medium, provided the source and authors are credited.

As our source, [CoVariants](https://CoVariants.org), we also recognize the great work of the Authors and laboratories
responsible for producing this data and sharing it via the GISAID Initiative:

```
Elbe, S., and Buckland-Merrett, G. (2017) Data, disease and diplomacy: GISAID’s innovative contribution to global health. Global Challenges, 1:33-46. DOI: 10.1002/gch2.1018PMCID: 31565258
```
