import os
from os.path import basename
from zipfile import ZipFile

import jsonpickle
import jsonpickle.ext.pandas as jsonpickle_pd
from django.shortcuts import render, redirect

from main import mba
from main.forms import FileInputForm, CampignForm
from main.models import Rule, Customer
from main.nbo.NBO import NBO
from . import validators
from .validators import getfile

jsonpickle_pd.register_handlers()


def index(request):
    return render(request, 'main/index.html')


def analytics(request):
    if request.method == 'POST':
        form = FileInputForm(request.POST, request.FILES)
        if form.is_valid():
            # files = ['file_transactions', 'file_goods', 'file_customers']
            # fs = FileSystemStorage()
            #
            # urls = {}
            # for file_name in files:
            #     file = request.FILES[file_name]
            #     name = fs.save(file.name, file)
            #     url = fs.url(name)
            #     urls[file_name] = url
            #     print(url)

            df_transactions = validators.getfile(request.FILES['file_transactions'])
            df_goods = getfile(request.FILES['file_goods'])
            df_customers = getfile(request.FILES['file_customers'])

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
    # products = list(rules.values_list('cluster_class', 'left', 'right', 'confidence'))
    #
    # limits = []
    # for product in products:
    #     limits.append(f'{product[0]} кластер: При покупке "{product[1]}" "{product[2]}" покупается в {product[3]}%')
    # print(limits)

    limits = [rule.__str__() for rule in rules]

    if request.method == 'POST':
        form = CampignForm(request.POST)
        if form.is_valid():
            print("VALID!")
            limits_value = request.POST.getlist("limits")

            phone_cost = request.POST['phone_cost']
            sms_cost = request.POST['sms_cost']
            email_cost = request.POST['email_cost']
            phone_percent = request.POST['phone_percent']
            sms_percent = request.POST['sms_percent']
            email_percent = request.POST['email_percent']
            calls_limit = request.POST['calls_limit']
            budget = request.POST['budget']
            cheque_up = request.POST['cheque_up']
            min = request.POST['min']
            sale = request.POST['sale']

            nbo = NBO(rules_ids, limits_value,
                      phone_cost, sms_cost, email_cost,
                      phone_percent, sms_percent, email_percent,
                      calls_limit, budget, cheque_up, min, sale)

            request.session['rules'] = jsonpickle.encode(nbo.rules_final)
            request.session['clusters'] = nbo.clusters
            request.session['revenue'] = nbo.revenue
            request.session['costs'] = nbo.total_cost

            return redirect('final')
    form = CampignForm()

    context = {
        'form': form,
        'limits': limits
    }

    return render(request, 'main/campaign.html', context=context)


def final(request):
    rules = jsonpickle.decode(request.session.get('rules'))
    clusters = request.session.get('clusters')
    revenue = request.session.get('revenue')
    costs = request.session.get('costs')

    context = {
        'rules': rules,
        'clusters': clusters,
        'revenue': revenue,
        'costs': costs
    }


    create_zip()


    return render(request, 'main/final.html', context=context)




def create_zip():
    with ZipFile('Результаты.zip', 'w') as zipObj:
        # Iterate over all the files in directory
        for folderName, subfolders, filenames in os.walk('./media'):
            for filename in filenames:
                print(filename)
                # create complete filepath of file in directory
                filePath = os.path.join(folderName, filename)
                # Add file to zip
                zipObj.write(filePath, basename(filePath))
