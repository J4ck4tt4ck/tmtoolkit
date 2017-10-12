# -*- coding: utf-8 -*-
from __future__ import division

import numpy as np
import pandas as pd


from ..utils import pickle_data, unpickle_file


def top_n_from_distribution(distrib, top_n=10, row_labels=None, val_labels=None):
    """
    Get `top_n` values from LDA model's distribution `distrib` as DataFrame. Can be used for topic-word distributions
    and document-topic distributions. Set `row_labels` to a prefix (pass a string) or a list. Set `val_labels` to
    return value labels instead of pure values (probabilities).
    """
    if row_labels is None:
        row_label_fixed = 'row'
    elif type(row_labels) is str:
        row_label_fixed = row_labels
    else:
        row_label_fixed = None

    if val_labels is not None and type(val_labels) in (list, tuple):
        val_labels = np.array(val_labels)

    df = pd.DataFrame(columns=range(top_n))

    for i, row_distrib in enumerate(distrib):
        if row_label_fixed:
            row_name = '%s %d' % (row_label_fixed, i+1)
        else:
            row_name = row_labels[i]

        # `sorter_arr` is an array of indices that would sort another array by `row_distrib` (from low to high!)
        sorter_arr = np.argsort(row_distrib)

        if val_labels is None:
            sorted_vals = row_distrib[sorter_arr][:-(top_n + 1):-1]
        else:
            if type(val_labels) is str:
                sorted_vals = ['%s %d' % (val_labels, num+1) for num in sorter_arr[::-1]][:top_n]
            else:
                # first brackets: sort vocab by `sorter_arr`
                # second brackets: slice operation that reverts ordering (:-1) and then selects only `n_top` number of
                # elements
                sorted_vals = val_labels[sorter_arr][:-(top_n + 1):-1]

        top_labels_series = pd.Series(sorted_vals, name=row_name)

        df = df.append(top_labels_series)

    return df


def _join_value_and_label_dfs(vals, labels, row_labels=None):
    df = pd.DataFrame()
    for i, (_, row) in enumerate(labels.iterrows()):
        joined = []
        for j, lbl in enumerate(row):
            val = vals.iloc[i, j]
            joined.append('%s (%f)' % (lbl, val))

        if row_labels is not None:
            if type(row_labels) is str:
                row_name = '%s %d' % (row_labels, i)
            else:
                row_name = row_labels[i]
        else:
            row_name = None

        df = df.append(pd.Series(joined, name=row_name))

    df.columns = pd.Series(range(1, df.shape[1]+1), name='rank')

    return df


def ldamodel_top_topic_words(topic_word_distrib, vocab, n_top=10):
    df_values = top_n_from_distribution(topic_word_distrib, top_n=n_top, row_labels='topic', val_labels=None)
    df_labels = top_n_from_distribution(topic_word_distrib, top_n=n_top, row_labels='topic', val_labels=vocab)
    return _join_value_and_label_dfs(df_values, df_labels, row_labels='topic')


def ldamodel_top_doc_topics(doc_topic_distrib, doc_labels, n_top=3):
    df_values = top_n_from_distribution(doc_topic_distrib, top_n=n_top, row_labels=doc_labels, val_labels=None)
    df_labels = top_n_from_distribution(doc_topic_distrib, top_n=n_top, row_labels=doc_labels, val_labels='topic')
    return _join_value_and_label_dfs(df_values, df_labels, row_labels=doc_labels)


def ldamodel_full_topic_words(topic_word_distrib, vocab, fmt_rownames='topic %d'):
    if fmt_rownames:
        rownames = [fmt_rownames % num for num in range(topic_word_distrib.shape[0])]
    else:
        rownames = None

    return pd.DataFrame(topic_word_distrib, columns=vocab, index=rownames)


def ldamodel_full_doc_topics(doc_topic_distrib, doc_labels, fmt_colnames='topic %d'):
    if fmt_colnames:
        colnames = [fmt_colnames % num for num in range(doc_topic_distrib.shape[0])]
    else:
        colnames = None

    return pd.DataFrame(doc_topic_distrib, columns=colnames, index=doc_labels)


def print_ldamodel_distribution(distrib, row_labels, val_labels, top_n=10):
    """
    Print `n_top` top values from a LDA model's distribution `distrib`. Can be used for topic-word distributions and
    document-topic distributions.
    """

    df_values = top_n_from_distribution(distrib, top_n=top_n, row_labels=row_labels, val_labels=None)
    df_labels = top_n_from_distribution(distrib, top_n=top_n, row_labels=row_labels, val_labels=val_labels)

    for i, (ind, row) in enumerate(df_labels.iterrows()):
        print(ind)
        for j, label in enumerate(row):
            val = df_values.iloc[i, j]
            print('> #%d. %s (%f)' % (j + 1, label, val))


def print_ldamodel_topic_words(topic_word_distrib, vocab, n_top=10):
    """Print `n_top` values from a LDA model's topic-word distributions."""
    print_ldamodel_distribution(topic_word_distrib, row_labels='topic', val_labels=vocab, top_n=n_top)


def print_ldamodel_doc_topics(doc_topic_distrib, doc_labels, n_top=3):
    """Print `n_top` values from a LDA model's document-topic distributions."""
    print_ldamodel_distribution(doc_topic_distrib, row_labels=doc_labels, val_labels='topic', top_n=n_top)


def save_ldamodel_to_pickle(model, vocab, doc_labels, picklefile):
    """Save a LDA model as pickle file."""
    pickle_data({'model': model, 'vocab': vocab, 'doc_labels': doc_labels}, picklefile)


def load_ldamodel_from_pickle(picklefile):
    """Load a LDA model from a pickle file."""
    data = unpickle_file(picklefile)
    return data['model'], data['vocab'], data['doc_labels']


def dtm_to_gensim_corpus(dtm):
    import gensim

    # DTM with documents to words sparse matrix in COO format has to be converted to transposed sparse matrix in CSC
    # format
    dtm_t = dtm.transpose()
    if hasattr(dtm_t, 'tocsc'):
        dtm_sparse = dtm_t.tocsc()
    else:
        from scipy.sparse.csc import csc_matrix
        dtm_sparse = csc_matrix(dtm_t)

    return gensim.matutils.Sparse2Corpus(dtm_sparse)


def dtm_and_vocab_to_gensim_corpus(dtm, vocab):
    corpus = dtm_to_gensim_corpus(dtm)

    # vocabulary array has to be converted to dict with index -> word mapping
    id2word = {idx: w for idx, w in enumerate(vocab)}

    return corpus, id2word


def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)


def results_by_parameter(res, param, sort_by=None, sort_desc=False,
                         crossvalid_use_measurment='validation',
                         crossvalid_reduce=False,
                         crossvalid_reduce_fn=None):
    """
    Takes a list of evaluation results `res` returned by a LDA evaluation function (a list in the form
    `[(parameter_set_1, {'<metric_name>': result_1, ...}), ..., (parameter_set_n, {'<metric_name>': result_n, ...})]`)
    and returns a list with tuple pairs using  only the parameter `param` from the parameter sets in the evaluation
    results such that the returned list is
    `[(param_1, {'<metric_name>': result_1, ...}), ..., (param_n, {'<metric_name>': result_n, ...})]`.
    Optionally order either by parameter value (`sort_by=None` - the default) or by result metric
    (`sort_by='<metric name>'`).
    """
    if len(res) == 0:
        return []

    if crossvalid_use_measurment not in ('validation', 'training'):
        raise ValueError('`crossvalid_use_measurment` must be either "validation" or "training" to use the validation '
                         'or training measurements.')

    tuples = [(p[param], r) for p, r in res]

    if type(tuples[0][1]) in (list, tuple):  # cross validation results
        if len(tuples[0][1]) < 1 or len(tuples[0][1][0]) != 2:
            raise ValueError('invalid evaluation results from cross validation passed')

        mean = lambda x: sum(x) / len(x)
        crossvalid_reduce_fn = crossvalid_reduce_fn or mean

        use_measurements_idx = 0 if crossvalid_use_measurment == 'training' else 1
        measurements = [(p, [pair[use_measurements_idx] for pair in r]) for p, r in tuples]
        measurements_reduced = [(p, crossvalid_reduce_fn(r)) for p, r in measurements]

        sort_by_idx = 0 if sort_by is None else 1
        sorted_ind = argsort(list(zip(*measurements_reduced))[sort_by_idx])
        if sort_desc:
            sorted_ind = reversed(sorted_ind)

        if crossvalid_reduce:
            measurements = measurements_reduced
    else:   # single validation results
        params, metric_results = list(zip(*tuples))
        if sort_by:
            sorted_ind = argsort([r[sort_by] for r in metric_results])
        else:
            sorted_ind = argsort(params)

        if sort_desc:
            sorted_ind = reversed(sorted_ind)

        measurements = tuples

    return [measurements[i] for i in sorted_ind]


def plot_eval_results(plt, eval_results, metric=None, normalize_y=None):
    if type(eval_results) not in (list, tuple) or not eval_results:
        raise ValueError('`eval_results` must be a list or tuple with at least one element')

    if type(eval_results[0]) not in (list, tuple) or len(eval_results[0]) != 2:
        raise ValueError('`eval_results` must be a list or tuple containing a (param, values) tuple. '
                         'Maybe `eval_results` must be converted with `results_by_parameter`.')

    if normalize_y is None:
        normalize_y = metric is None

    if metric == 'cross_validation':
        plotting_res = []
        for k, folds in eval_results:
            plotting_res.extend([(k, val, f) for f, val in enumerate(folds)])
        x, y, f = zip(*plotting_res)
        fig, ax = plt.subplots()
        ax.scatter(x, y, c=f, alpha=0.5)
    else:
        if metric is not None and type(metric) not in (list, tuple):
            metric = [metric]
        elif metric is None:
            metric = sorted(next(iter(eval_results))[1].keys())

        if normalize_y:
            res_per_metric = {}
            for m in metric:
                params = list(zip(*eval_results))[0]
                unnorm = np.array([metric_res[m] for _, metric_res in eval_results])
                rng = np.max(unnorm) - np.min(unnorm)
                if np.max(unnorm) < 0:
                    norm = -(np.max(unnorm) - unnorm) / rng
                else:
                    norm = (unnorm-np.min(unnorm)) / rng
                res_per_metric[m] = dict(zip(params, norm))

            eval_results_tmp = []
            for k, _ in eval_results:
                metric_res = {}
                for m in metric:
                    metric_res[m] = res_per_metric[m][k]
                eval_results_tmp.append((k, metric_res))
            eval_results = eval_results_tmp

        fig, ax = plt.subplots()
        x = list(zip(*eval_results))[0]
        for m in metric:
            y = [metric_res[m] for _, metric_res in eval_results]
            ax.plot(x, y, label=m)
        ax.legend(loc='best')

