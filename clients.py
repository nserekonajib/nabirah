def calculate_salaries(total_earnings, salary_percentage, investments):
    salary_pool = total_earnings * (salary_percentage / 100)
    total_investment = sum(investments.values())
    salaries = {
        partner: salary_pool * (amount / total_investment)
        for partner, amount in investments.items()
    }
    return salaries

# Example usage
earnings = 10_000_000  # UGX
salary_percent = 30  # 30% of earnings goes to salaries
investments = {
    "Partner A": 6_000_000,
    "Partner B": 4_000_000
}

salaries = calculate_salaries(earnings, salary_percent, investments)
print(salaries)
