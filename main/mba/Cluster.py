from main.models import Rule


class Cluster:

    def __init__(self, name, df):
        self.name = name
        # отстортированный списк правил для кластера.
        self.rules = self.get_rules(df)

    def get_rules(self, df, min_lift=0.5):
        result = []
        for index, row in df[df[df.columns[-1]] >= min_lift].iterrows():
            rule = Rule.objects.create(cluster_class=self.name,
                                       left=row[0],
                                       left_support=row[1],
                                       right=row[2],
                                       right_support=row[3],
                                       support=row[4],
                                       confidence=row[5],
                                       lift=row[6])
            result.append(rule)

        #Удаляем пару с наименьшим конфиденсом
        return result
