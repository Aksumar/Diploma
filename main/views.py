import jsonpickle
import jsonpickle.ext.pandas as jsonpickle_pd
import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect

from main import mba, nbo
from main.forms import FileInputForm, CampignForm
from main.models import Rule, Customer
from main.nbo.NBO import NBO

jsonpickle_pd.register_handlers()


def getfile(request, file):
    if '.csv' in file.name:
        df = pd.read_csv(file.name, index_col=0)
    else:
        df = pd.read_excel(file, index_col=0)
    return df


def index(request):
    return render(request, 'main/index.html')


def analytics(request):
    if request.method == 'POST':
        form = FileInputForm(request.POST, request.FILES)
        if form.is_valid():
            files = ['file_transactions', 'file_goods', 'file_customers']
            fs = FileSystemStorage()

            # urls = {}
            # for file_name in files:
            #     file = request.FILES[file_name]
            # name = fs.save(file.name, file)
            # url = fs.url(name)
            # urls[file_name] = url
            # print(url)

            # form.save()

            df_transactions = getfile(request, request.FILES['file_transactions'])
            df_goods = getfile(request, request.FILES['file_goods'])
            df_customers = getfile(request, request.FILES['file_customers'])

            print(df_transactions.columns, df_goods.columns, df_customers.columns)

            Rule.objects.all().delete()
            Customer.objects.all().delete()

            mba_obj = mba.mbaMethod(df_transactions, df_goods, df_customers,
                                    request.POST['min_conf'], request.POST['min_support'],
                                    request.POST['clusters'] == 'on')

            mba_obj.start_mba()

            return redirect('rule_choice')
    else:

        form = FileInputForm()

    context = {
        'form': form
    }
    return render(request, 'main/file_input.html', context=context)


def rule_choice(request):
    if request.method == 'POST':
        result = request.POST.getlist("checked_selection")
        request.session['rules_ids'] = result
        print(result)
        return redirect('campaign')

    clusters = Rule.objects.values_list('cluster_class').distinct()
    clusters = [list(elem)[0] for elem in clusters]
    if (len(clusters)) > 1:
        clusters = clusters[1:]

    rules = []
    for cluster in clusters:
        rules.append(Rule.objects.filter(cluster_class=cluster))

    context = {
        'clusters': clusters,
        'rules': rules,

    }

    return render(request, 'main/rule_choice.html', context=context)


def campaign(request):
    rules_ids = request.session.get('rules_ids')
    rules = Rule.objects.filter(id__in=rules_ids)
    products = list(rules.values_list('right', 'cluster_class'))

    limits = []
    for product in products:
        limits.append(f'{product[1]} кластер, товар - {product[0]}')
    print(limits)

    # nbo = NBO(rules_ids)

    if request.method == 'POST':
        form = CampignForm(request.POST)
        if form.is_valid():
            print("VALID!")
    form = CampignForm()

    context = {
        'form': form,
        'limits':limits
    }

    return render(request, 'main/campaign.html', context=context)


def final(request):
    return render(request, 'main/final.html')