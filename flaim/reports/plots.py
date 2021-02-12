from textwrap import wrap

import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
from numpy.linalg import LinAlgError
from plotly.express.colors import qualitative
from plotly.io import to_html


def nutrient_distribution_plot(df: pd.DataFrame):
    nutrients = ['sodium_dv', 'saturatedfat_dv', 'sugar']

    try:
        fig = ff.create_distplot(df[nutrients].dropna(how='all').fillna(0).T.values,
                                 ['Sodium', 'Saturated Fat', 'Sugar'], colors=qualitative.Vivid, histnorm='probability',
                                 bin_size=0.01, show_rug=False, )
        fig.update_layout(
            width=1100,
            font_size=18,
            xaxis=dict(
                title='Daily Value',
                tickformat='%',
                showgrid=True,
                range=[0, min([1, max(df[n].quantile(0.95) for n in nutrients)])]
            ),
            yaxis=dict(
                tickformat='%',
                title='Proportion of Products'
            ),
            margin=dict(
                l=100,
                r=20,
                b=30,
                t=30,
            ),
            legend_title='Nutrients'
        )

        fig.add_shape(dict(
            type='line',
            yref='paper',
            x0=0.15,
            y0=0,
            x1=0.15,
            y1=1,
            line=dict(
                color='Black',
                width=2
            )))

        fig.add_annotation(text='← Low in Nutrient',
                           yref='paper',
                           x=0.145, y=1,
                           showarrow=False,
                           xanchor='right',
                           yanchor='bottom',
                           font_color='green')
        fig.add_annotation(text='High in Nutrient →',
                           yref='paper',
                           x=0.155, y=1,
                           showarrow=False,
                           xanchor='left',
                           yanchor='bottom',
                           font_color='red')
    except LinAlgError:
        return "Graph can't be displayed."
    except ValueError:
        return "Not enough data to generate graph."

    return to_html(fig, include_plotlyjs=False, full_html=False)


def category_nutrient_distribution_plot(df: pd.DataFrame):
    def over_15(row):
        return 1 if row > 0.15 else 0

    nutrients = ['sodium_dv', 'saturatedfat_dv', 'sugar']
    nutrient_map = {'sodium_dv': 'Sodium', 'saturatedfat_dv': 'Saturated Fat', 'sugar': 'Sugar'}
    categories = ['Beverages', 'Cereals and Other Grain Products', 'Dairy Products and Substitutes',
                  'Meat and Poultry, Products and Substitutes', 'Snacks']

    category_labels = ['<br>'.join(wrap(c, 20)) for c in categories]

    plot_df = df.loc[df['category_text'].isin(categories)]

    for n in nutrients:
        plot_df[f'{n}_count'] = plot_df[n].apply(lambda row: over_15(row))

    plot_df = plot_df[['category_text'] + [f'{n}_count' for n in nutrients]].groupby(
        'category_text').sum().reindex(categories)

    data = [
        go.Bar(name=nutrient_map[nutrient], x=category_labels, y=plot_df[f'{nutrient}_count']) for nutrient in nutrients
    ]

    layout = dict(
        width=1100,
        font_size=18,
        margin=dict(
            l=100,
            r=20,
            b=20,
            t=30,
        ),
        yaxis_title='Products Exceeding Threshold',
        xaxis=dict(
            title='Food Category',
            showgrid=True,
            tickson='boundaries',
            tickangle=0,
        ),
    )

    fig = go.Figure(data=data, layout=layout)

    return to_html(fig, include_plotlyjs=False, full_html=False)
