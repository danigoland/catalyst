import json
import os
import pickle
import re

from catalyst.assets._assets import TradingPair
from six.moves.urllib import request
from datetime import date, datetime

import pandas as pd

from catalyst.exchange.exchange_errors import ExchangeSymbolsNotFound, \
    InvalidHistoryFrequencyError
from catalyst.utils.paths import data_root, ensure_directory, \
    last_modified_time

SYMBOLS_URL = 'https://s3.amazonaws.com/enigmaco/catalyst-exchanges/' \
              '{exchange}/symbols.json'


def get_exchange_folder(exchange_name, environ=None):
    """
    The root path of an exchange folder.

    :param exchange_name:
    :param environ:
    :return:
    """
    if not environ:
        environ = os.environ

    root = data_root(environ)
    exchange_folder = os.path.join(root, 'exchanges', exchange_name)
    ensure_directory(exchange_folder)

    return exchange_folder


def get_exchange_symbols_filename(exchange_name, environ=None):
    """
    The absolute path of the exchange's symbol.json file.

    :param exchange_name:
    :param environ:
    :return:
    """
    exchange_folder = get_exchange_folder(exchange_name, environ)
    return os.path.join(exchange_folder, 'symbols.json')


def download_exchange_symbols(exchange_name, environ=None):
    """
    Downloads the exchange's symbols.json from the repository.

    :param exchange_name:
    :param environ:
    :return: response
    """
    filename = get_exchange_symbols_filename(exchange_name)
    url = SYMBOLS_URL.format(exchange=exchange_name)
    response = request.urlretrieve(url=url, filename=filename)
    return response


def get_exchange_symbols(exchange_name, environ=None):
    """
    The de-serialized content of the exchange's symbols.json.

    :param exchange_name:
    :param environ:
    :return:
    """
    filename = get_exchange_symbols_filename(exchange_name)

    if not os.path.isfile(filename) or \
                    pd.Timedelta(pd.Timestamp('now',
                                              tz='UTC') - last_modified_time(
                        filename)).days > 1:
        download_exchange_symbols(exchange_name, environ)

    if os.path.isfile(filename):
        with open(filename) as data_file:
            data = json.load(data_file)
            return data
    else:
        raise ExchangeSymbolsNotFound(
            exchange=exchange_name,
            filename=filename
        )


def get_symbols_string(assets):
    """
    A concatenated string of symbols from a list of assets.

    :param assets:
    :return:
    """
    array = [assets] if isinstance(assets, TradingPair) else assets
    return ', '.join([asset.symbol for asset in array])


def get_exchange_auth(exchange_name, environ=None):
    """
    The de-serialized contend of the exchange's auth.json file.

    :param exchange_name:
    :param environ:
    :return:
    """
    exchange_folder = get_exchange_folder(exchange_name, environ)
    filename = os.path.join(exchange_folder, 'auth.json')

    if os.path.isfile(filename):
        with open(filename) as data_file:
            data = json.load(data_file)
            return data
    else:
        data = dict(name=exchange_name, key='', secret='')
        with open(filename, 'w') as f:
            json.dump(data, f, sort_keys=False, indent=2,
                      separators=(',', ':'))
            return data


def get_algo_folder(algo_name, environ=None):
    """
    The algorithm root folder of the algorithm.

    :param algo_name:
    :param environ:
    :return:
    """
    if not environ:
        environ = os.environ

    root = data_root(environ)
    algo_folder = os.path.join(root, 'live_algos', algo_name)
    ensure_directory(algo_folder)

    return algo_folder


def get_algo_object(algo_name, key, environ=None, rel_path=None):
    """
    The de-serialized object of the algo name and key.

    :param algo_name:
    :param key:
    :param environ:
    :param rel_path:
    :return:
    """
    if algo_name is None:
        return None

    folder = get_algo_folder(algo_name, environ)

    if rel_path is not None:
        folder = os.path.join(folder, rel_path)

    filename = os.path.join(folder, key + '.p')

    if os.path.isfile(filename):
        try:
            with open(filename, 'rb') as handle:
                return pickle.load(handle)
        except Exception as e:
            return None
    else:
        return None


def save_algo_object(algo_name, key, obj, environ=None, rel_path=None):
    """
    Serialize and save an object by algo name and key.

    :param algo_name:
    :param key:
    :param obj:
    :param environ:
    :param rel_path:
    :return:
    """
    folder = get_algo_folder(algo_name, environ)

    if rel_path is not None:
        folder = os.path.join(folder, rel_path)
        ensure_directory(folder)

    filename = os.path.join(folder, key + '.p')

    with open(filename, 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)


def get_algo_df(algo_name, key, environ=None, rel_path=None):
    """
    The de-serialized DataFrame of an algo name and key.

    :param algo_name:
    :param key:
    :param environ:
    :param rel_path:
    :return:
    """
    folder = get_algo_folder(algo_name, environ)

    if rel_path is not None:
        folder = os.path.join(folder, rel_path)

    filename = os.path.join(folder, key + '.csv')

    if os.path.isfile(filename):
        try:
            with open(filename, 'rb') as handle:
                return pd.read_csv(handle, index_col=0, parse_dates=True)
        except IOError:
            return pd.DataFrame()
    else:
        return pd.DataFrame()


def save_algo_df(algo_name, key, df, environ=None, rel_path=None):
    """
    Serialize to csv and save a DataFrame by algo name and key.

    :param algo_name:
    :param key:
    :param df:
    :param environ:
    :param rel_path:
    :return:
    """
    folder = get_algo_folder(algo_name, environ)

    if rel_path is not None:
        folder = os.path.join(folder, rel_path)
        ensure_directory(folder)

    filename = os.path.join(folder, key + '.csv')

    with open(filename, 'wt') as handle:
        df.to_csv(handle, encoding='UTF_8')


def get_exchange_minute_writer_root(exchange_name, environ=None):
    """
    The minute writer folder for the exchange.

    :param exchange_name:
    :param environ:
    :return:
    """
    exchange_folder = get_exchange_folder(exchange_name, environ)

    minute_data_folder = os.path.join(exchange_folder, 'minute_data')
    ensure_directory(minute_data_folder)

    return minute_data_folder


def get_exchange_bundles_folder(exchange_name, environ=None):
    """
    The temp folder for bundle downloads by algo name.

    :param exchange_name:
    :param environ:
    :return:
    """
    exchange_folder = get_exchange_folder(exchange_name, environ)

    temp_bundles = os.path.join(exchange_folder, 'temp_bundles')
    ensure_directory(temp_bundles)

    return temp_bundles


def perf_serial(obj):
    """
    JSON serializer for objects not serializable by default json code

    :param obj:
    :return:
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    raise TypeError("Type %s not serializable" % type(obj))


def get_common_assets(exchanges):
    """
    The assets available in all specified exchanges.

    :param exchanges:
    :return:
    """
    symbols = []
    for exchange_name in exchanges:
        s = [asset.symbol for asset in exchanges[exchange_name].get_assets()]
        symbols.append(s)

    inter_symbols = set.intersection(*map(set, symbols))

    assets = []
    for symbol in inter_symbols:
        for exchange_name in exchanges:
            asset = exchanges[exchange_name].get_asset(symbol)
            assets.append(asset)

    return assets


def get_frequency(freq, data_frequency):
    if freq == 'daily':
        freq = '1d'
    elif freq == 'minute':
        freq = '1m'

    freq_match = re.match(r'([0-9].*)(m|M|d|D)', freq, re.M | re.I)
    if freq_match:
        candle_size = int(freq_match.group(1))
        unit = freq_match.group(2)

    else:
        raise InvalidHistoryFrequencyError(freq)

    if unit.lower() == 'd':
        if data_frequency == 'minute':
            data_frequency = 'daily'

    elif unit.lower() == 'm':
        if data_frequency == 'daily':
            data_frequency = 'minute'

    else:
        raise InvalidHistoryFrequencyError(freq)

    return candle_size, unit, data_frequency


def resample_history_df(df, candle_size, field):
    if candle_size > 1:
        if field == 'open':
            agg = 'first'
        elif field == 'high':
            agg = 'max'
        elif field == 'low':
            agg = 'min'
        elif field == 'close':
            agg = 'last'
        elif field == 'volume':
            agg = 'sum'
        else:
            raise ValueError('Invalid field.')

        # TODO: pad with nan?
        return df.resample('{}T'.format(candle_size)).agg(agg)

    else:
        return df