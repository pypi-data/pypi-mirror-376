"""
Solution for marginal values implementation.
"""

import random

def calculate_marginal_value(goods, selected_good, valuation_function, bids, prices):
    """
    Compute the marginal value of selected_good: 
    the difference between the valuation of the bundle that includes the good and the bundle without it.
    A bidder wins a good if bid >= price.
    """
    # Determine which goods the bidder would win with current bids
    won_goods = {g for g in goods if bids.get(g, 0) >= prices.get(g, 0) and g != selected_good}
    valuation_without = valuation_function(won_goods)
    won_goods_with = won_goods.union({selected_good})
    valuation_with = valuation_function(won_goods_with)
    return valuation_with - valuation_without

def calculate_expected_marginal_value(goods, selected_good, valuation_function, bids, price_distribution, num_samples=50):
    """
    Compute the expected marginal value of selected_good:
    the average of the marginal values over a number of samples.
    """
    total_mv = 0.0
    for _ in range(num_samples):
        sample_prices = price_distribution.sample()
        mv = calculate_marginal_value(goods, selected_good, valuation_function, bids, sample_prices)
        total_mv += mv
    return total_mv / num_samples
