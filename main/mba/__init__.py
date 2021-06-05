import itertools

import jsonpickle
import numpy as np
import pandas as pd
from main.models import Customer

from main.mba.Cluster import Cluster

LEFT = 'LEFT'
RIGHT = 'RIGHT'
LEFT_SUPPORT = 'LEFT_SUPPORT'
RIGHT_SUPPORT = 'RIGHT_SUPPORT'
SUPPORT = 'SUPPORT'
LIFT = 'LIFT'
CONFIDENCE = 'CONFIDENCE'
MARGIN_LEFT = 'MARGIN_LEFT'
MARGIN_RIGHT = 'MARGIN_RIGHT'


class mbaMethod:
    ref_dict = {}

    def __init__(self, df_transactions, df_goods, df_customers, min_conf, min_sup, with_clusters):
        # список товаров в чековых транзакциях. Из них создаем пары
        self.product_list = df_transactions.columns[1:].values
        print(self.product_list)

        # К кааким кластерам принадлежат клиенты
        self.clusters = sorted(df_customers.iloc[:, 0].unique())
        print(self.clusters)

        # Сохраняем данные в словарь
        self.transactions = df_transactions.to_dict()
        self.goods = df_goods.to_dict()
        self.customers = df_customers.to_dict()

        # МИнимальный конфиденс и саппорт
        self.min_conf = float(min_conf)
        self.min_sup = float(min_sup)

        # Необходим ли анализ по кластерам
        self.with_clusters = with_clusters

        # Лист описаний кластеров
        self.cluster_list = []

        # клиенты
        self.create_customers(df_transactions, with_clusters)

        print(Customer.objects.first())
        print(Customer.objects.last())

    # Расчет значения support для товаров и пар
    def support_count(self, df, products, min_support=0.01, number=2):
        result_pairs = {}

        for i in range(1, number + 1):
            pairs = self.create_pairs(products, number=i)

            for pair in pairs:
                if i == 1:
                    pair = [pair]
                support_pair = len(df[df[pair].sum(axis=1) >= len(pair)]) / len(df)
                if support_pair < min_support:
                    if i == 1 and pair[0] in products:
                        products = products[products != pair[0]]
                else:
                    result_pairs[tuple(sorted(pair))] = support_pair

            if i == 1:
                result_pairs = {list(k)[0]: v for k, v in result_pairs.items()}

        result_pairs = dict(sorted(result_pairs.items(), key=lambda item: item[1], reverse=True))
        return result_pairs

    # все возможные сочетания товаров длиной number
    def create_pairs(self, item_list, number=1):
        if number == 1:
            return item_list

        result = list(itertools.permutations(item_list, number))
        return [list(elem) for elem in result]

        # mba-анализ для заданной матрицы и для заданных продуктов

    # формирование правил
    def mba(self, df, products, itemset_len=2, min_conf=0.01, min_support=0.01, ):
        self.ref_dict = self.support_count(df, products, number=itemset_len)

        print(self.ref_dict)

        itemsets = self.create_pairs(products, number=itemset_len)

        print(itemsets)

        columns = [LEFT, LEFT_SUPPORT,
                   RIGHT, RIGHT_SUPPORT,
                   SUPPORT, CONFIDENCE]

        df_result = pd.DataFrame(columns=columns)

        i = 0
        for itemset in itemsets:
            left = itemset[0]
            right = itemset[1]

            left_support = self.ref_dict.get(left, 0)
            right_support = self.ref_dict.get(right, 0)
            itemset_support = self.ref_dict.get(tuple(sorted(itemset)), 0)

            if itemset_support >= min_support:
                df_result.loc[i] = [left,
                                    left_support,
                                    right,
                                    right_support,
                                    # support if itemset
                                    itemset_support,
                                    # confidence of itemset
                                    itemset_support / left_support if left_support != 0 else 0]

            i += 1

        df_result = df_result.drop_duplicates([LEFT, RIGHT])

        df_result = df_result[df_result[CONFIDENCE] >= min_conf]
        df_result = df_result[df_result[SUPPORT] >= min_support]

        df_result[LIFT] = df_result[CONFIDENCE] / df_result[RIGHT_SUPPORT]

        for c in [LEFT_SUPPORT, RIGHT_SUPPORT, CONFIDENCE, SUPPORT, LIFT]:
            df_result[c] = df_result[c].astype(float)

        df_result = df_result.sort_values(by=[LIFT, CONFIDENCE, SUPPORT], ascending=False)

        df_result = df_result.round(3)

        return df_result

        # Расчет маржинальности : из цены вычитается цена закупки.

    # расчет маржинальности
    def margin(self, df_info):
        return df_info[:, 0] - df_info[:, 1]

    def process(self, df_transactions):
        df_mba = self.mba(df_transactions,
                          self.product_list, min_conf=self.min_conf, min_support=self.min_sup)

        df_goods = pd.DataFrame.from_dict(self.goods)
        df_goods_info = pd.DataFrame(df_goods.iloc[:, 0] - df_goods.iloc[:, 1], columns=['Маржа'])
        df_mba = pd.merge(df_mba, df_goods_info, left_on=RIGHT, right_index=True)
        df_mba = pd.merge(df_mba, df_goods_info, left_on=LEFT, right_index=True)

        df_mba.columns = np.append(df_mba.columns[:-2].values, [MARGIN_LEFT, MARGIN_RIGHT])

        # Убираем те пары, в которых есть отрицательная маржинальность
        df_mba = df_mba[df_mba[MARGIN_LEFT] > 0]
        df_mba = df_mba[df_mba[MARGIN_RIGHT] > 0]

        # Убираем данные о маржинальности
        df_mba.drop(columns=[MARGIN_LEFT, MARGIN_RIGHT], inplace=True)

        for col in [LEFT_SUPPORT, RIGHT_SUPPORT, SUPPORT, CONFIDENCE]:
            df_mba[col] = np.round(pd.to_numeric(df_mba[col]) * 100, 1)

        # Сортируем
        df_mba.sort_values([LIFT, CONFIDENCE, SUPPORT],
                           ascending=[False, False, False], inplace=True)
        return df_mba

    def create_customers(self, df, with_clusters):
        x = df.groupby(df.columns[0]).sum()
        y = df.groupby(df.columns[0]).sum().sum(axis=1)
        for c in x.columns:
            x[c] = x[c] / y

        if with_clusters:
            df_clients = pd.DataFrame.from_dict(self.customers)
            x = pd.merge(left=df_clients, left_index=True, right=x,
                         right_index=True)

            x.to_csv('media/СводнаяТаблица.csv', index=True)

            # columns_to_dict = x.columns[4:]
            # print(columns_to_dict)
            #
            # for index, row in x[:5].iterrows():
            #     dict = row[columns_to_dict].to_dict()
            #     dict = jsonpickle.encode(dict)
            #
            #     Customer.objects.create(customer_id=row[x.columns[0]],
            #                             cluster_id=row[x.columns[1]],
            #                             mean_cheque=row[x.columns[2]],
            #                             return_proba=row[x.columns[3]],
            #                             purchases=dict)

    def start_mba(self):
        # all
        df_transactions = pd.DataFrame().from_dict(self.transactions)
        df_result = self.process(df_transactions)

        cluster = Cluster("all", df_result)
        print(cluster.name)

        for rule in cluster.rules:
            print(rule)
        print("\n")
        self.cluster_list.append(cluster)

        df_result.to_excel('media/mba_analysis_result.xlsx', sheet_name='mba_ALL', index=False)

        if self.with_clusters:
            # к транзакциям добавляем кластер
            df_clients = pd.DataFrame.from_dict(self.customers)
            df_transactions = pd.merge(left=df_transactions, left_on=df_transactions.columns[0],
                                       right=df_clients[[df_clients.columns[0]]],
                                       right_index=True)

            print(self.clusters)
            for group in self.clusters:
                df_group = df_transactions[df_transactions.iloc[:, -1] == group]

                df_group_result = self.process(df_group)

                cluster = Cluster(group, df_group_result)
                print(cluster.name)

                for rule in cluster.rules:
                    print(rule)
                print("\n")
                self.cluster_list.append(cluster)

                with pd.ExcelWriter('media/mba_analysis_result.xlsx', engine='openpyxl', mode='a') as writer:
                    df_group_result.to_excel(writer, sheet_name=f'mba_{group}_cluster', index=False)
