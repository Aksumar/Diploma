import pandas as pd
from ortools.linear_solver import pywraplp

from main.models import Rule


class NBO:

    def __init__(self, ids):

        flag = False
        while not flag:
            try:
                f = open(r'C:\Users\li.iskhakova\PycharmProjects\ClientAnalytics\media\pivot.csv')
                flag = True
                f.close()
            except IOError:
                print("File not accessible")

        pivot = pd.read_csv(r'C:\Users\li.iskhakova\PycharmProjects\ClientAnalytics\media\pivot.csv', index_col=0)
        rules = Rule.objects.filter(id__in=ids)

        clusters = rules.values('cluster_class').distinct()
        clusters = list(clusters.values_list('cluster_class', flat=True))

        print(clusters)

        df_result = pd.DataFrame(index=pivot.index)

        # для каждого правила необходимо составить рейтинг
        for cluster in clusters:
            for rule in rules.filter(cluster_class=cluster):
                left = rule.left
                right = rule.right
                confidence = rule.confidence

                df_result[rule.__str__()] = pivot[pivot.columns[2]] * pivot[left] * confidence * pivot[right].apply(
                    lambda x: 0 if x > 0 else 1) * pivot[pivot.columns[0]].apply(
                    lambda x: 1 if x == cluster else 0)

        df_result.to_excel('df_result.xlsx', index=True)

    def analyse(self):

        df = pd.read_csv(r'C:\Users\li.iskhakova\PycharmProjects\ClientAnalytics\media\pivot.csv', index_col=0)

        costs = df.to_numpy()
        print(len(costs))
        print(len(costs[0]))
        num_workers = len(costs)
        num_tasks = len(costs[0])

        # Solver
        # Create the mip solver with the SCIP backend.
        solver = pywraplp.Solver.CreateSolver('SCIP')

        x = {}
        for i in range(num_workers):
            for j in range(num_tasks):
                x[i, j] = solver.IntVar(0, 1, '')

        # Ограничение на кол-во акций на человека
        for i in range(num_workers):
            solver.Add(solver.Sum([x[i, j] for j in range(num_tasks)]) <= 1)



        solver.Add(solver.Sum([x[i, 0] for i in range(num_workers)]) <= 100)
        solver.Add(solver.Sum([x[i, 1] for i in range(num_workers)]) <= 20)

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
                        print('Customer %d assigned to offer %d.  Cost = %f' %
                              (i, j + 1, costs[i][j]))
                        # ids.append(i)
                        # tasks.append(j + 1)
