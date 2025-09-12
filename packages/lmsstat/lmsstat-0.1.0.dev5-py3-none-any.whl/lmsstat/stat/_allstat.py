import pandas as pd

from ._posthoc import dunn_test, scheffe_test
from ._tests import anova_test, kruskal_test, t_test, u_test
from ._utils import p_adjust, preprocess_data


def allstats(data, p_adj=True):
    """
    Generates a statistical analysis of the given file.

    Parameters:
        data (str): Data to be analyzed.

        P_adj (bool, optional): Whether to perform p-value adjustment. Defaults to True.

    Returns:
        pandas.DataFrame: The statistical analysis results.
    """
    _, groups_split, metabolite_names = preprocess_data(data)

    num_groups = len(groups_split)

    if num_groups <= 1:
        raise ValueError("Number of groups must be greater than 1")

    result_t = t_test(groups_split, metabolite_names)
    result_u = u_test(groups_split, metabolite_names)
    if num_groups > 2:
        result_anova = anova_test(groups_split, metabolite_names)
        result_kruskal = kruskal_test(groups_split, metabolite_names)
        result_scheffe = scheffe_test(groups_split, metabolite_names)
        result_dunn = dunn_test(groups_split, metabolite_names)

    if p_adj:
        result_t = p_adjust(result_t)
        result_u = p_adjust(result_u)
        if num_groups > 2:
            result_anova = p_adjust(result_anova)
            result_kruskal = p_adjust(result_kruskal)
    if num_groups == 2:
        return pd.concat([result_t, result_u], axis=1)
    else:
        return pd.concat(
            [
                result_t,
                result_u,
                result_anova,
                result_scheffe,
                result_kruskal,
                result_dunn,
            ],
            axis=1,
        )
