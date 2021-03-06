# Generated by Django 2.1.1 on 2018-09-08 20:47

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tags', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Scheduler',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=255, verbose_name='Label')),
                ('date', models.DateField(default=datetime.date.today, verbose_name='Date')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Amount')),
                ('currency', models.CharField(editable=False, max_length=3, verbose_name='Currency')),
                ('status', models.CharField(choices=[('active', 'Active'), ('ignored', 'Ignored'), ('inactive', 'Inactive')], default='active', help_text='Depending on its value, determine whether it could alter the bank account balance or being used by statistics.', max_length=32, verbose_name='Status')),
                ('reconciled', models.BooleanField(default=False, help_text='Whether the bank transaction has been applied on the real bank account.', verbose_name='Reconciled')),
                ('payment_method', models.CharField(choices=[('credit_card', 'Credit card'), ('cash', 'Cash'), ('transfer', 'Transfer'), ('transfer_internal', 'Transfer internal'), ('check', 'Check')], default='credit_card', max_length=32, verbose_name='Payment method')),
                ('memo', models.TextField(blank=True, verbose_name='Memo')),
                ('type', models.CharField(choices=[('monthly', 'Monthly'), ('weekly', 'Weekly')], default='monthly', help_text='The type of recurrence to be applied.', max_length=32, verbose_name='Type')),
                ('recurrence', models.PositiveSmallIntegerField(blank=True, help_text='How many time the bank transaction should be cloned.', null=True, verbose_name='Recurrence')),
                ('last_action', models.DateTimeField(editable=False, help_text='Last time the scheduled bank transaction has been cloned.', null=True)),
                ('state', models.CharField(choices=[('waiting', 'Waiting'), ('finished', 'Finished'), ('failed', 'Failed')], default='waiting', editable=False, help_text='State of the scheduled bank transaction.', max_length=32)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedulers', to='accounts.Account')),
                ('tag', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='schedulers', to='tags.Tag', verbose_name='Tag')),
            ],
            options={
                'db_table': 'schedulers',
            },
        ),
        migrations.AddIndex(
            model_name='scheduler',
            index=models.Index(fields=['state', 'last_action'], name='schedulers_state_5021e9_idx'),
        ),
    ]
