import pandas as pd
from ortools.linear_solver import pywraplp

from main.models import Rule


class NBO:

    def __init__(self, ids, limits, phone_cost, sms_cost, email_cost,
                 phone_percent, sms_percent, email_percent,
                 calls_limit, budget, cheque_up, min, sale):

        flag = False
        while not flag:
            try:
                f = open(r'C:\Users\li.iskhakova\PycharmProjects\ClientAnalytics\media\СводнаяТаблица.csv')
                flag = True
                f.close()
            except IOError:
                print("File not accessible")

        pivot = pd.read_csv(r'C:\Users\li.iskhakova\PycharmProjects\ClientAnalytics\media\СводнаяТаблица.csv',
                            index_col=0)
        rules = Rule.objects.filter(id__in=ids)

        clusters = rules.values('cluster_class').distinct()
        clusters = list(clusters.values_list('cluster_class', flat=True))

        print(clusters)

        df_result = pd.DataFrame(index=pivot.index)

        # для каждого правила необходимо составить рейтинг
        for cluster in clusters:

            for rule_name in rules.filter(cluster_class=cluster):
                left = rule_name.left
                right = rule_name.right
                confidence = rule_name.confidence

                df_result[rule_name.__str__()] = pivot[pivot.columns[2]] * pivot[left] * confidence \
                                                 * pivot[right].apply(
                    lambda x: 0 if x > 0 else 1) * pivot[pivot.columns[0]].apply(
                    lambda x: 1 if str(x) == cluster else 0)

        mean_cluster_cheque = pivot[pivot.columns[:2]].groupby(pivot.columns[0]).mean()
        mean_cluster_cheque.columns = ['cheque']

        df_result.to_excel(r'./media/Ratings.xlsx', index=True)
        dict_rule_customers = self.analyse(df_result, limits, rules, pivot)

        # определяем вид коммуникации

        max_calls_per_rule = int(int(calls_limit) / len(rules))

        rules_final = []

        for rule in rules:
            r_final = Rule_Final(name=rule.__str__(),
                                 cluster=rule.cluster_class,
                                 left=rule.left,
                                 right=rule.right,
                                 confidence=rule.confidence,
                                 phone_cost=phone_cost,
                                 sms_cost=sms_cost,
                                 email_cost=email_cost,
                                 phone_percent=phone_percent,
                                 sms_percent=float(sms_percent) * 0.01,
                                 email_percent=float(email_percent) * 0.01,
                                 max_calls=max_calls_per_rule,
                                 budget=float(budget) / len(rules),
                                 cheque=mean_cluster_cheque.loc[int(rule.cluster_class)]['cheque'],
                                 cheque_up=cheque_up,
                                 min=min,
                                 sale=sale,
                                 customers=dict_rule_customers[rule.__str__()])
            rules_final.append(r_final)

        self.save(rules_final)

        total_costs = sum([rule.total_cost for rule in rules_final])
        total_revenue = sum([rule.total_revenue for rule in rules_final])

        self.rules_final = rules_final
        self.clusters = clusters
        self.total_cost = round(total_costs, 2)
        self.revenue = round(total_revenue, 2)

    def analyse(self, df, limits, rules, pivot):
        costs = df.to_numpy()
        print(len(costs))
        print(len(costs[0]))
        num_workers = len(costs)
        num_tasks = len(costs[0])

        # Solver
        # Create the mip solver with the SCIP backend.
        solver = pywraplp.Solver.CreateSolver('SCIP')

        dict_result = {}
        for rule in rules:
            dict_result[rule.__str__()] = []

        x = {}
        for i in range(num_workers):
            for j in range(num_tasks):
                x[i, j] = solver.IntVar(0, 1, '')

        # Ограничение на кол-во акций на человека
        for i in range(num_workers):
            solver.Add(solver.Sum([x[i, j] for j in range(num_tasks)]) <= 1)

        for j in range(num_tasks):
            solver.Add(solver.Sum([x[i, j] for i in range(num_workers)]) <= int(limits[j]))

        # Objective
        objective_terms = []
        for i in range(num_workers):
            for j in range(num_tasks):
                objective_terms.append(costs[i][j] * x[i, j])

        solver.Maximize(solver.Sum(objective_terms))

        # Solve
        status = solver.Solve()

        # Print solution.
        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            print('Total cost = ', solver.Objective().Value(), '\n')
            for i in range(num_workers):
                for j in range(num_tasks):
                    # Test if x[i,j] is 1 (with tolerance for floating point arithmetic).
                    if x[i, j].solution_value() > 0.5:
                        # print('Customer %d assigned to offer %d.  Rating = %f' %
                        #       (i, j + 1, costs[i][j]))
                        contacts = dict_result[rules[j].__str__()]
                        contacts.append(Customer(pivot.index[i], costs[i][j], rules[j].__str__()))
                        dict_result[rules[j].__str__()] = contacts

        for k, v in dict_result.items():
            dict_result[k] = sorted(v, key=lambda customer: customer.rating, reverse=True)

        for k, v in dict_result.items():
            for customer in v:
                print(customer)

        return dict_result
        # pd.DataFrame(dict([(k, pd.Series(v)) for k, v in dict_result.items()])) \
        #     .to_excel('./media/Контакты.xlsx')

    def save(self, rules):
        rule = rules[0]
        print(rule)
        df = pd.DataFrame.from_records([c.to_dict() for c in rule.customers])
        print(rule.__str__()[:30])
        i = 1
        df.to_excel('media/Контакты.xlsx', sheet_name=f'правило{i}', index=False)

        for rule in rules[1:]:
            i = i +1
            print(rule)
            df = pd.DataFrame.from_records([c.to_dict() for c in rule.customers])

            with pd.ExcelWriter('media/Контакты.xlsx', engine='openpyxl', mode='a') as writer:
                df.to_excel(writer, sheet_name=f'{rule.__str__()[:30]}', index=False)


def calculate_numbers(phone_max, phone_cost, sms_cost, email_cost, budget, people, email_percent,
                      sms_percent):
    solver = pywraplp.Solver.CreateSolver('SCIP')

    infinity = solver.infinity()
    # x and y are integer non-negative variables.
    phone_number = solver.IntVar(0.0, infinity, 'phone_number')
    sms_number = solver.IntVar(0.0, infinity, 'sms_number')
    email_number = solver.IntVar(0.0, infinity, 'email_number')

    solver.Add(phone_number <= phone_max)
    solver.Add(phone_cost * phone_number + sms_cost * sms_number + email_cost * email_number <= budget)
    solver.Add(phone_number + sms_number + email_number == people)
    solver.Add(email_number >= people * email_percent)
    solver.Add(sms_number >= (sms_percent / email_percent) * email_number)

    print('Number of constraints =', solver.NumConstraints())

    solver.Maximize(phone_number)
    status = solver.Solve()

    x, y, z = 0, 0, 0

    if status == pywraplp.Solver.OPTIMAL:
        print('Solution:')
        print('Objective value =', solver.Objective().Value())
        print('x =', phone_number.solution_value())
        print('y =', sms_number.solution_value())
        print('z =', email_number.solution_value())
        print(
            phone_cost * phone_number.solution_value() + sms_cost * sms_number.solution_value() + email_cost * email_number.solution_value())

        x = phone_number.solution_value()
        y = sms_number.solution_value()
        z = email_number.solution_value()
    else:

        print('The problem does not have an optimal solution.')

    return x, y, z


class Customer(object):
    def __init__(self, id_param, rating, rule):
        self.id = id_param
        self.rating = rating
        self.rule = rule
        self.contact_type = None

    def set_contact_type(self, contact_type):
        self.contact_type = contact_type

    def __str__(self):
        return f"{self.id} {self.rating}"

    def __hash__(self):
        return self.id

    def to_dict(self):
        return {
            'id': self.id,
            'rating': self.rating,
            'rule': self.rule,
            'contact_type': self.contact_type
        }


class Rule_Final(object):
    def __init__(self, name, cluster, left, right, confidence, phone_cost, sms_cost, email_cost,
                 phone_percent, sms_percent, email_percent,
                 max_calls, budget, cheque, cheque_up, min, sale, customers):
        self.cluster = cluster
        self.name = name
        self.left = left
        self.right = right
        self.confidence = float(confidence)
        self.phone_cost = float(phone_cost)
        self.sms_cost = float(sms_cost)
        self.email_cost = float(email_cost)
        self.phone_percent = float(phone_percent)
        self.sms_percent = float(sms_percent)
        self.email_percent = float(email_percent)
        self.budget = float(budget)
        self.cheque_up = float(cheque_up)
        self.min = float(min)
        self.sale = int(sale)
        self.cheque = float(cheque)
        self.customers = customers

        self.phone_total_cost = None
        self.sms_total_cost = None
        self.email_total_cost = None
        self.total_cost = None
        self.total_revenue = None

        self.set_contact_type_to_customers(max_calls)

    def __str__(self):

        return f"{self.cluster} {self.left} -> {self.right} " \
               f"чек: {self.cheque} cost: {self.total_cost} revenue:{self.total_revenue} "

    def calls_limit(self, max_calls):
        temp = int(len(self.customers) * self.phone_percent)
        return min(max_calls, temp)

    def set_contact_type_to_customers(self, max_calls):
        total_customers_number = len(self.customers)

        phone_number = self.calls_limit(max_calls)

        x, y, z = calculate_numbers(phone_max=phone_number,
                                    phone_cost=self.phone_cost,
                                    sms_cost=self.sms_cost,
                                    email_cost=self.email_cost,
                                    budget=self.budget,
                                    people=len(self.customers),
                                    email_percent=self.email_percent,
                                    sms_percent=self.sms_percent)

        self.phone_number = int(x)
        self.sms_number = int(y)
        self.email_number = int(z)

        self.phone_total_cost = round(phone_number * self.phone_cost,2)
        self.sms_total_cost = round(self.sms_number * self.sms_cost,2)
        self.email_total_cost = round(self.email_number * self.email_cost,2)



        self.total_cost = self.phone_total_cost + self.sms_total_cost + self.email_total_cost


        self.new_cheque = int(round((self.cheque + self.cheque_up + self.total_cost / len(
            self.customers)) / (1 - self.sale * 0.01), -2))

        self.cheque = round(self.cheque, 2)

        self.total_revenue = round(total_customers_number * self.cheque * self.min * 0.01 - self.total_cost,2)

        for c in range(0, self.phone_number):
            self.customers[c].set_contact_type('phone')

        for c in range(self.phone_number, self.phone_number + self.sms_number):
            self.customers[c].set_contact_type('sms')

        if (not (self.phone_number == 0 and self.sms_number == 0 and self.email_number == 0)):
            for c in range(self.phone_number + self.sms_number, total_customers_number):
                self.customers[c].set_contact_type('email')
