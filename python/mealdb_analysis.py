from requests import Session
from requests_futures.sessions import FuturesSession

import matplotlib.pyplot as plt
import numpy as np

# Endpoints used to make requests to mealdb
MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1/"
GET_ALL_CATEGORIES = MEALDB_BASE_URL + "categories.php"
GET_RECIPES_BY_CATEGORY = MEALDB_BASE_URL + "filter.php?c=%s"
GET_CANADIAN = MEALDB_BASE_URL + "filter.php?a=Canadian"
GET_MEAL_BY_ID = MEALDB_BASE_URL + "lookup.php?i=%s"

# Constants used for data extraction
LABELS = 0
COUNTS = 1


def perform_analysis():
    """
    Makes requests necessary to visualize and analyze which categories have most recipes
    and which ingredient is least used in Canadian deserts.
    """

    # Initialize sessions for making HTTPS requests (synchronous and asynchronous)
    session = Session()
    futures_session = FuturesSession()

    # Queue up requests for analysis
    # Synchronous requests
    categories = get_categories(session)
    canadian_recipe_ids = get_canadian_recipes(session)

    # Asynchronous requests
    category_tuples = get_recipe_counts(futures_session, categories)
    canadian_dessert_ingredient_counts = get_dessert_ingredient_count(futures_session, canadian_recipe_ids)

    # Extract category and ingredient labels and counts for data visualization
    category_labels = extract_category_information(category_tuples, LABELS)
    category_counts = extract_category_information(category_tuples, COUNTS)
    ingredient_labels = canadian_dessert_ingredient_counts.keys()
    ingredient_counts = extract_ingredient_counts(canadian_dessert_ingredient_counts, ingredient_labels)

    # Generate answers to analysis
    print_max_categories(category_tuples)
    print_min_ingredients(canadian_dessert_ingredient_counts)

    # Plot data in graphs
    plot_bars(category_labels, category_counts, ingredient_labels, ingredient_counts)


def print_min_ingredients(canadian_dessert_ingredient_counts):
    """
    Prints answer to Canadian dessert question given list of ingredients and counts.
    :param canadian_dessert_ingredient_counts: list of dessert ingredients and counts
    """

    ingredient_tuples = canadian_dessert_ingredient_counts.items()

    # Find categor(ies) with most recipes
    counts = {}

    # Create hash table to map counts to categories
    for ingredient in ingredient_tuples:
        count = ingredient[1]
        ingredient_name = ingredient[0]
        if count not in counts:
            counts[count] = [ingredient_name]
        else:
            counts[count].append(str(ingredient_name))

    # Find max count and list of categories for that count
    min_count = min(counts.keys())
    min_ingredients = counts[min_count]

    # Print results
    print('Q2: Which Canadian dessert ingredient(s) has the fewest recipes?')
    if len(min_ingredients) > 1:
        print('A2: The ingredients used the least in Canadian dessert recipes are %s, which have %d recipes each.' % (str(min_ingredients), min_count))
    else:
        print('A2: The ingredient used the least in Canadian dessert recipes is %s, having %d recipes.' % (min_ingredients[0], min_count))


def print_max_categories(category_tuples):
    """
    Prints answer to category question given list of categories and counts.
    :param category_tuples: list of items from category counts
    """

    # Find categor(ies) with most recipes
    counts = {}

    # Create hash table to map counts to categories
    for category in category_tuples:
        if category[1] not in counts:
            counts[category[1]] = [category[0]]
        else:
            counts[category[1]].append(str(category[0]))

    # Find max count and list of categories for that count
    max_count = max(counts.keys())
    max_categories = counts[max_count]

    # Print results
    print('Q1: Which categor(ies) has most recipes?')
    if len(max_categories) > 1:
        print('A1: The categories with the most recipes are %s, which have %d recipes each.' % (str(max_categories), max_count))
    else:
        print('A1: The category with the most recipes is %s, having %d recipes.' % (max_categories[0], max_count))


def extract_ingredient_counts(ingredients_dict, ingredient_labels):
    """
    Extract ingredient counts from dict for plotting in chart.
    :param ingredients_dict: dict mapping ingredient names to counts
    :param ingredient_labels: list of strings containing ingredient names
    :return: list of counts of ingredients
    """

    return [ingredients_dict[ingredient] for ingredient in ingredient_labels]


def extract_category_information(category_tuples, element):
    """
    Returns a list of category strings or counts extracted from the tuples in the input list.
    :param category_tuples: list of tuples in the form of (name, count)
    :param element: 0 for labels and 1 for counts
    :return: list of strings representing the category names
    """

    if element > 1 or element < 0:
        print("Invalid element value provided to extract category information.")
        return None

    return [category[element] for category in category_tuples]


def get_categories(session):
    """
    Synchronously retrieves all categories from mealdb API as JSON.
    :return: Returns a list of strings of category names.
    """

    response_json = session.get(GET_ALL_CATEGORIES).json()
    categories = process_categories(response_json)
    print("There are %d categories of meal in mealdb." % len(categories))

    return categories


def get_canadian_recipes(session):
    """
    Returns a list of all ID's for meals that are canadian and desserts
    :param session: Session
    :return: list<string>
    """

    response_json = session.get(GET_CANADIAN).json()
    meals = response_json['meals']
    print("There are %d Canadian recipes in mealdb" % len(meals))
    id_list = [meal['idMeal'] for meal in meals]

    return id_list


def process_categories(json):
    """
    Returns a list of category names required for querying the mealdb recipe filter endpoint.
    :param json: Dict containing category objects from mealdb categories endpoint.
    :return: Returns a list of strings.
    """

    categories = [category['strCategory'] for category in json['categories']]

    return categories


def get_recipe_counts(futures_session, categories):
    """
    Retrieves recipes for all categories in request and returns a list of categories and counts
    :param futures_session: a futures session used to make concurrent asynchronous requests
    :param categories: list of strings representing meal categories
    :return: list of tuples, containing category name and count of recipes
    """

    # Make a request to the filter endpoint for each category and count recipes
    results = [queue_category(futures_session, category) for category in categories]
    results = [(category[0], len(category[1].json()['meals'])) for category in results]

    # List of tuples containing category and count of recipes
    return results


def queue_category(futures_session, category):
    """
    Queues an asynchronous request to mealdb for a given category name and extracts json from response.
    :param futures_session: FutureSession
    :param category: String
    :return: tuple (category name (string), response json (dict))
    """

    return (category, futures_session.get(GET_RECIPES_BY_CATEGORY % category).result())


def get_dessert_ingredient_count(futures_session, meal_ids):
    """
    Requests ingredient lists and develops counts given a list of dessert ID's
    :param futures_session: FutureSession
    :param meal_ids: list<meal id: string>
    :return: list<(ingredient, count)>
    """

    ingredient_counts = {}

    meal_responses = [futures_session.get(GET_MEAL_BY_ID % meal_id).result().json()['meals'][0] for meal_id in meal_ids]
    meal_responses = list(filter(lambda meal : meal['strCategory'] == 'Dessert', meal_responses))
    print("There are %d Canadian desserts in the mealdb." % len(meal_responses))
    [process_dessert_json(result, ingredient_counts) for result in meal_responses]

    return ingredient_counts


def process_dessert_json(dessert_json, ingredient_counts):
    """
    Adds counts of ingredients to hashmap given a dessert
    :param dessert_json:
    :param ingredient_counts:
    """

    keys = list(dessert_json.keys())
    filtered_keys = list(filter(lambda dessert_key: is_invalid_dessert_key(dessert_key, dessert_json), keys))

    for key in filtered_keys:
        lower_key = dessert_json[key]
        if lower_key is None:
            break
        else:
            lower_key = lower_key.lower()
            if lower_key in ingredient_counts:
                ingredient_counts[lower_key] += 1
            else:
                ingredient_counts[lower_key] = 1


def is_invalid_dessert_key(dessert_key, dessert_json):
    """
    Returns true if key is not blank or an empty string.
    :param dessert_key:
    :param dessert_json:
    :return:
    """

    prefix = 'strIngredient'
    return str(dessert_key).startswith(prefix) and dessert_json[dessert_key] not in (' ', '')


def plot_bars(category_labels, category_counts, ingredient_labels, ingredient_counts):
    """
    Plots recipe counts by category in a bar graph using Matplotlib.
    :param category_labels: list of strings (category names)
    :param category_counts: list of ints (recipe counts)
    :param ingredient_labels: list of strings (ingredient names)
    :param ingredient_counts: list of ints (ingredient counts)
    """
    # Plots a bar graph of categories and counts
    plt.figure(figsize=(8,8))
    category_index = np.arange(len(category_labels))
    plt.subplot(2, 1, 1)
    plt.bar(category_index, category_counts)
    plt.ylabel('No of Recipes', fontsize=5)
    plt.xticks(category_index, category_labels, fontsize=5, rotation=0)
    plt.title('Counts of Recipes by Category from MealDB')

    ingredient_index = np.arange(len(ingredient_labels))
    plt.subplot(2, 1, 2)
    plt.bar(ingredient_index, ingredient_counts)
    plt.xlabel('Ingredient', fontsize=5)
    plt.ylabel('No of Recipes', fontsize=5)
    plt.xticks(ingredient_index, ingredient_labels, fontsize=5, rotation=90)
    plt.title('Counts of Canadian Dessert Recipes by Ingredient from MealDB')

    plt.show()


def main():
    perform_analysis()


if __name__ == "__main__":
    main()
