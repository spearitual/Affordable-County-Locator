import panel as pn
import pandas as pd
import matplotlib
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("agg")

pn.extension('ipywidgets')

### Part 0: Getting data

@pn.cache # Add caching to only download data once
def get_data():
    #df = pd.read_excel('fbc_data_2024.xlsx', sheet_name='County', header=1)
    df = pd.read_excel('https://files.epi.org/uploads/fbc_data_2024.xlsx', sheet_name='County', header=1)
    
    #Drop unneeded columns
    col_to_drop = list(df.columns[:1]) + list(df.columns[13:21])
    df = df.drop(columns=col_to_drop)

    #One apparently random county is missing median income data, but is still ranked.
    #By taking the average of the counties ranked immediately above and below it, a quick estimate of $55,122 can be made.
    df.fillna(55122.0,inplace=True)

    df['median_family_income'] = df['median_family_income'].astype('int64')

    #Add leading zeroes to FIPS codes makes them readable to Tableau.
    df['county_fips'] = df['county_fips'].astype(str).str.zfill(5)

    df.columns = ['state_abbr','FIPS','county','family','housing','food','transportation','healthcare',
                  'other_necessities','childcare','taxes','total','median_family_income',
                  'num_counties_in_st','st_cost_rank','st_med_aff_rank','st_income_rank']
    
    #Some counties share names across states; adding their state code makes them unique.
    df['county_state'] = df.county + ', ' + df.state_abbr
    
    df['median_monthly_family_income'] = df.median_family_income.div(12).round(0).astype('int64')
    
    df['remaining_money'] = df.median_monthly_family_income - df.total
    return df

df = get_data()

### Part 1: Find and display model budget

#Function to represent data in US dollars
def dol(value,df,row=0):
    return '${:0,}'.format(df[value][row])

#Function that takes user input and displays the corresponding row from the df
def calculate_model(user_county,user_parents,user_children):
    user_family = f'{user_parents}p{user_children}c'
    user_df = df.loc[(df.county_state == user_county) & (df.family == user_family)].reset_index(drop=True)
    return (
        f'Moderately frugal families of {user_parents} {"adult" if user_parents == "1" else "adults"} and {user_children} {"child" if user_children == 1 else "children"} living in {user_county} '
        'tend to have a monthly family budget similar to the following:\n'
        f'\nHousing: {dol("housing",user_df)}'
        f'\nFood: {dol("food",user_df)}'
        f'\nTransportation: {dol("transportation",user_df)}'
        f'\nHealthcare: {dol("healthcare",user_df)}'
        f'\nChildcare: {dol("childcare",user_df)}'
        f'\nOther necessities: {dol("other_necessities",user_df)}'
        f'\nTaxes: {dol("taxes",user_df)}'
        f'\nTotal: {dol("total",user_df)}'
        f'\n\nThe median monthly family income for {user_county} is {dol("median_monthly_family_income",user_df)}, which would '
        f'leave {dol("remaining_money",user_df)} each month for emergencies, saving, and discretionary spending.'
    )

#Widgets for receiving user input
user_county = pn.widgets.AutocompleteInput(
    name='County of primary residence:', options=df.county_state.unique().tolist(),
    case_sensitive=False,
    placeholder='Input county name')

adult_title = pn.pane.Markdown('Number of adults in household:') #Radio buttons don't have their name displayed as a title, so I add it here
user_parents = pn.widgets.RadioButtonGroup(
    options=['1', '2'], button_type='default', margin=(12,0,0,0))

user_children = pn.widgets.IntSlider(
    name='Number of children', start=0, end=4, step=1, value=0)

#Bind widgets to function
county_model = pn.bind(calculate_model, user_county=user_county,user_parents=user_parents,user_children=user_children)

#Submit button
county_submit = pn.widgets.Button(name="Submit Family/Location", button_type="primary")

#Function to make model function respond to submit button
def county_result(clicked):
    if clicked:
        if user_county.value == '':
            return 'County information is required.'
        return county_model()
    return "Click Submit Family/Location to see a typical budget."

#Binding button to button function
county_result = pn.pane.Markdown(pn.bind(county_result,county_submit))


### Part 2: Calculate and display user budget's comparison to model

#Function to calculate the user budget's comparison to the model. Accounts for dividing by zero.
def calculate_percentage(user_value,column,df):
    if df[column][0] == 0:
        return 1.0
    else:
        return 1+round(((user_value-df[column][0])/df[column][0]),3)

#Function that takes user budget input and returns how it compares to model.
def calculate_budget_percentage(user_county,user_parents,user_children,user_income,user_housing,user_food,user_transportation,user_healthcare,user_childcare,user_other,user_taxes):
    #Repeated code. Could potentially be avoided with more binding, but that wouldn't change performance
    user_family = f'{user_parents}p{user_children}c'
    user_df = df.loc[(df.county_state == user_county) & (df.family == user_family)].reset_index(drop=True)
    #New code
    income_p = calculate_percentage(user_income,'median_monthly_family_income',user_df)
    housing_p = calculate_percentage(user_housing,'housing',user_df)
    food_p = calculate_percentage(user_food,'food',user_df)
    transportation_p = calculate_percentage(user_transportation,'transportation',user_df)
    healthcare_p = calculate_percentage(user_healthcare,'healthcare',user_df)
    childcare_p = calculate_percentage(user_childcare,'childcare',user_df)
    other_p = calculate_percentage(user_other,'other_necessities',user_df)
    taxes_p = calculate_percentage(user_taxes,'taxes',user_df)
    total_p = 1+round((((user_housing+user_food+user_transportation+user_healthcare+
                     user_childcare+user_other+user_taxes)-user_df.total[0])/user_df.total[0]),3)
    return (
        f"Your family's income is {income_p:.1%} that of the median family income in your area. "
        'Your budget compares to the typical model as follows:\n'
        f'\nHousing: {housing_p:.1%}'
        f'\nFood: {food_p:.1%}'
        f'\nTransportation: {transportation_p:.1%}'
        f'\nHealthcare: {healthcare_p:.1%}'
        f'\nChildcare: {"N/A" if user_children==0 else str(round(childcare_p*100,1))+"%"}'
        f'\nOther necessities: {other_p:.1%}'
        f'\nTaxes: {taxes_p:.1%}'
        f'\nTotal: {total_p:.1%}'
    )

#Function for budget-input widgets
def input_budget(prompt):
    return pn.widgets.IntInput(name=prompt, value=0, start=0)

#Budget input widgets
user_income = input_budget('What is your monthly family income? (Pre-tax.)')
budget_title = pn.pane.Markdown("#### For each item, input your family's monthly spending.")
                          #How much do you spend on housing per month? Inclu
user_housing = input_budget('Housing (Include utilities.)')
user_food = input_budget('Food')
user_transportation = input_budget('Transportation (Gas, car payment/repair, bus pass, etc.)')
user_healthcare = input_budget('Healthcare (Both out-of-pocket and premium)')
user_childcare = input_budget('Childcare')
user_other = input_budget('Other necessities (Clothes, house/school supplies, etc.)')
user_taxes = input_budget('Taxes')

#Binding widgets to function
budget_percentage = pn.bind(calculate_budget_percentage,user_county,user_parents,user_children,user_income,user_housing,user_food,user_transportation,user_healthcare,user_childcare,user_other,user_taxes)

#Submit button, function to respond to button, binding to button
budget_submit = pn.widgets.Button(name="Submit Budget", button_type="primary")

def budget_result(clicked):
    if clicked:
        if user_county.value == '':
            return 'County information is required.'
        return budget_percentage()
    return "Click Submit Budget to see how your budget compares."

budget_result = pn.pane.Markdown(pn.bind(budget_result,budget_submit))


### Part 3: Calculate and display most afforable counties and budgets

#Function to take user constraints, find most affordable counties, and calculate budgets
def calculate_comparison(user_county,user_parents,user_children,user_income,user_housing,user_food,user_transportation,user_healthcare,user_childcare,user_other,user_taxes,
                  bring_income,income_cap,income_cap_amount,include_all_states,states_allowed,result_count):
    #Repeated code:
    user_family = f'{user_parents}p{user_children}c'
    user_df = df.loc[(df.county_state == user_county) & (df.family == user_family)].reset_index(drop=True)
    income_p = calculate_percentage(user_income,'median_monthly_family_income',user_df)
    housing_p = calculate_percentage(user_housing,'housing',user_df)
    food_p = calculate_percentage(user_food,'food',user_df)
    transportation_p = calculate_percentage(user_transportation,'transportation',user_df)
    healthcare_p = calculate_percentage(user_healthcare,'healthcare',user_df)
    childcare_p = calculate_percentage(user_childcare,'childcare',user_df)
    other_p = calculate_percentage(user_other,'other_necessities',user_df)
    taxes_p = calculate_percentage(user_taxes,'taxes',user_df)
    #New code:
    new_df = df.loc[(df.family == user_family)].reset_index(drop=True)
    if bring_income:
        new_df.median_monthly_family_income = user_income
    else:
        new_df.median_monthly_family_income = new_df.median_monthly_family_income.mul(income_p).round(0).astype('int64')
    new_df['median_monthly_family_income_uncapped'] = new_df.median_monthly_family_income
    if income_cap:
        new_df.median_monthly_family_income.clip(upper=income_cap_amount,inplace=True)
    if not include_all_states:
        new_df = new_df.loc[(new_df.state_abbr.isin(states_allowed))].reset_index(drop=True)
    new_df.housing = new_df.housing.mul(housing_p).round(0).astype('int64')
    new_df.food = new_df.food.mul(food_p).round(0).astype('int64')
    new_df.transportation = new_df.transportation.mul(transportation_p).round(0).astype('int64')
    new_df.healthcare = new_df.healthcare.mul(healthcare_p).round(0).astype('int64')
    new_df.other_necessities = new_df.other_necessities.mul(other_p).round(0).astype('int64')
    new_df.childcare = new_df.childcare.mul(childcare_p).round(0).astype('int64')
    new_df.taxes = new_df.taxes.mul(taxes_p).round(0).astype('int64')
    new_df.total = new_df.housing + new_df.food + new_df.transportation + new_df.healthcare + new_df.other_necessities + new_df.childcare + new_df.taxes
    new_df.remaining_money = new_df.median_monthly_family_income - new_df.total
    new_df = new_df.sort_values('remaining_money',ascending=False).reset_index(drop=True)
    county_results = []
    limit = result_count
    if limit > len(new_df):
        limit = len(new_df)
        county_results.append(f'There are only {limit} counties to show!\n\n')
    if limit == 1:
        second_line = 'here is the most affordable county for your family, along with what your budget might look living there:\n'
    else:
        second_line = f'here are the {limit} most affordable counties for your family, along with what your budget might look living there:\n'
    if not bring_income and not income_cap:
        county_results.append("With both your spending and income recalculated based on each county's norm, "
                             + second_line)
    elif bring_income:
        county_results.append("With your exact income maintained but your spending recalculated based on each county's norm, "
                          + second_line)
    else:
        county_results.append(f"With both your spending and income recalculated based on each county's norm (and an income cap of ${income_cap_amount:,.0f}), "
                          + second_line)
    for i in range(limit):
        current_result = [f'\n#{i+1}\n{new_df.county_state[i]}']
        for [j,k] in [['housing','Housing'],['food','Food'],['transportation','Transportation'],['healthcare','Healthcare'],
                      ['childcare','Childcare'],['other_necessities','Other necessities'],['taxes','Taxes'],['total','Total'],
                      ['median_monthly_family_income','Income'],['remaining_money','Remaining money']]:
            if j == 'median_monthly_family_income' and income_cap == True and new_df.median_monthly_family_income_uncapped[i] > new_df.median_monthly_family_income[i]:
                current_result.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{k}: {dol(j,new_df,row=i)} (Uncapped: {dol('median_monthly_family_income_uncapped',new_df,row=i)})")
            else:
                current_result.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{k}: {dol(j,new_df,row=i)}")
        county_results.append('\n'.join(current_result))
    return '\n'.join(county_results)

#Constraint widgets
bring_income_title = pn.pane.Markdown('Maintain income exactly, regardless of county:')
bring_income = pn.widgets.Switch(margin=(19,0,0,0))

income_cap_title = pn.pane.Markdown('Enforce income cap:')
income_cap = pn.widgets.Switch(margin=(19,0,0,0),disabled=bring_income)

income_cap_amount = pn.widgets.IntInput(name='Income cap value:', value=0, start=0,disabled= bring_income)

include_all_states_title = pn.pane.Markdown('Include all states:')
include_all_states = pn.widgets.Switch(margin=(19,0,0,0),value=True)

states_allowed = pn.widgets.MultiChoice(name='States to include:', options=df.state_abbr.unique().tolist(),disabled= include_all_states) #Would be nice to disable when include_all_states is not active

result_count = pn.widgets.IntInput(name='Results to view:', value=5, start=1)

#Bind to widgets
comparison = pn.bind(calculate_comparison, user_county,user_parents,user_children,
                     user_income,user_housing,user_food,user_transportation,user_healthcare,user_childcare,user_other,user_taxes,
                     bring_income,income_cap,income_cap_amount,include_all_states,states_allowed,result_count)

#Submit button, bind
comparison_submit = pn.widgets.Button(name="Submit Constraints", button_type="primary")

def comparison_result(clicked):
    if clicked:
        if user_county.value == '':
            return 'County information is required.'
        return comparison()
    return "Click Submit Constraints to see the final results."

comparison_result = pn.pane.Markdown(pn.bind(comparison_result,comparison_submit))


### Part 4: Bar chart of results
def calculate_bar(user_county,user_parents,user_children,user_income,user_housing,user_food,user_transportation,user_healthcare,user_childcare,user_other,user_taxes,
                  bring_income,income_cap,income_cap_amount,include_all_states,states_allowed,result_count,bar_type):
    #Repeated code:
    user_family = f'{user_parents}p{user_children}c'
    user_df = df.loc[(df.county_state == user_county) & (df.family == user_family)].reset_index(drop=True)
    income_p = calculate_percentage(user_income,'median_monthly_family_income',user_df)
    housing_p = calculate_percentage(user_housing,'housing',user_df)
    food_p = calculate_percentage(user_food,'food',user_df)
    transportation_p = calculate_percentage(user_transportation,'transportation',user_df)
    healthcare_p = calculate_percentage(user_healthcare,'healthcare',user_df)
    childcare_p = calculate_percentage(user_childcare,'childcare',user_df)
    other_p = calculate_percentage(user_other,'other_necessities',user_df)
    taxes_p = calculate_percentage(user_taxes,'taxes',user_df)
    new_df = df.loc[(df.family == user_family)].reset_index(drop=True)
    if bring_income:
        new_df.median_monthly_family_income = user_income
    else:
        new_df.median_monthly_family_income = new_df.median_monthly_family_income.mul(income_p).round(0).astype('int64')
    new_df['median_monthly_family_income_uncapped'] = new_df.median_monthly_family_income
    if income_cap:
        new_df.median_monthly_family_income.clip(upper=income_cap_amount,inplace=True)
    if not include_all_states:
        new_df = new_df.loc[(new_df.state_abbr.isin(states_allowed))].reset_index(drop=True)
    new_df.housing = new_df.housing.mul(housing_p).round(0).astype('int64')
    new_df.food = new_df.food.mul(food_p).round(0).astype('int64')
    new_df.transportation = new_df.transportation.mul(transportation_p).round(0).astype('int64')
    new_df.healthcare = new_df.healthcare.mul(healthcare_p).round(0).astype('int64')
    new_df.other_necessities = new_df.other_necessities.mul(other_p).round(0).astype('int64')
    new_df.childcare = new_df.childcare.mul(childcare_p).round(0).astype('int64')
    new_df.taxes = new_df.taxes.mul(taxes_p).round(0).astype('int64')
    new_df.total = new_df.housing + new_df.food + new_df.transportation + new_df.healthcare + new_df.other_necessities + new_df.childcare + new_df.taxes
    new_df.remaining_money = new_df.median_monthly_family_income - new_df.total
    new_df = new_df.sort_values('remaining_money',ascending=False).reset_index(drop=True)
    #New code:
    new_df = new_df[:result_count]
    fig = Figure(figsize=(result_count,3))
    ax = fig.add_subplot(111)
    if bar_type == 'Stacked':
        stacked_value=True
    else:
        stacked_value=False
    ax = new_df[['remaining_money','housing','food','transportation','healthcare','childcare','other_necessities','taxes']].plot.bar(
        stacked=stacked_value, width=0.8, ax=ax, color=['limegreen','wheat','gold','paleturquoise','salmon','violet','silver','dimgrey'])
    ax.legend(labels=['Remaining Money','Housing','Food','Transportation','Healthcare','Childcare','Other','Taxes'],reverse=True,loc="upper right",bbox_to_anchor=(1 + 2.41/result_count, 1))
    ax.set_xticks(ticks=np.arange(len(new_df)),labels=new_df.county_state.values)
    ax.yaxis.set_major_formatter('${x:,.0f}')
    ax.yaxis.grid(linestyle='--',alpha=.4)
    ax.set_xlim([-.5, len(new_df)-.5])
    plt.close(fig)
    return fig

def nothing_fig():
    fig = Figure(figsize=(5,4))
    ax = fig.add_subplot(111)
    return fig

bar_type_title = pn.pane.Markdown('Type of bar chart:')
bar_type = pn.widgets.RadioButtonGroup(
    options=['Stacked', 'Clustered'], button_type='default', margin=(12,0,0,0))

bar = pn.bind(calculate_bar, user_county,user_parents,user_children,
                     user_income,user_housing,user_food,user_transportation,user_healthcare,user_childcare,user_other,user_taxes,
                     bring_income,income_cap,income_cap_amount,include_all_states,states_allowed,result_count,bar_type)

def bar_result(clicked):
    if clicked:
        if user_county.value == '':
            return nothing_fig()
        return bar()
    return nothing_fig()

bar_result = pn.pane.Matplotlib(pn.bind(bar_result,comparison_submit), dpi=144, tight=True)


### Part 5: Templating

template = pn.template.BootstrapTemplate(title='Affordable County Locator')

#Sidebar formatting
intro = pn.pane.Markdown('If you and your family could maintain your relative income and spending habits, '
                         'in which US county would you be able to save the most money every month? Use this app to find out! '
                         'Check out the README in the "Files" tab to the top-right for detailed instructions, take-aways, and sources.')
part1_title = pn.pane.Markdown('## Part 1: County and family size')
part2_title = pn.pane.Markdown('## Part 2: Budget')
part3_title = pn.pane.Markdown('## Part 3: Calculation constraints')

template.sidebar.extend([intro, part1_title, user_county, pn.Row(adult_title, user_parents), user_children, county_submit,
                         part2_title, user_income, budget_title, user_housing, user_food, user_transportation, user_healthcare, user_childcare, user_other, user_taxes, budget_submit,
                         part3_title, pn.Row(bring_income_title, bring_income),pn.Row(income_cap_title, income_cap),income_cap_amount,pn.Row(include_all_states_title, include_all_states),states_allowed,result_count,pn.Row(bar_type_title,bar_type),comparison_submit])

#Main formatting
main1 = pn.Card(
    county_result,
    title='Typical Budget',
    styles={'background': 'WhiteSmoke'}
)
main2 = pn.Card(
    budget_result,
    title='Budget Comparison',
    styles={'background': 'WhiteSmoke'}
)
main3 = pn.Card(
    comparison_result,
    title='Most Affordable Counties',
    styles={'background': 'WhiteSmoke'},
    max_height = 300
)
main4 = pn.Card(
    bar_result,
    title='Most Affordable Counties, bar chart',
    styles={'background':'WhiteSmoke'}
)
template.main.append(
    pn.Column(main1,main2,main3,main4)
)

template.servable();
