import numpy as np


class AntGotLostException(Exception):
    pass


def initiate_pheromones(score_graph):
    import numpy as np

    norm = np.sqrt(np.nansum(np.square(score_graph)))

    return score_graph/norm


def get_next_city(current_city, city_extra_points, pheromone_levels, punishment_graph, alpha, beta):

    available_pheromone_levels = pheromone_levels[:, current_city, :]
    punishment_matrix = punishment_graph[:, current_city, :]
    # score_matrix = (1+city_extra_points) / punishment_matrix
    score_matrix = 1/punishment_matrix

    probability_matrix = available_pheromone_levels**alpha * score_matrix**beta
    probability_matrix = probability_matrix / np.nansum(probability_matrix)  # normalize

    cumulative_prob_vector = np.nancumsum(probability_matrix)

    r = np.random.rand()
    winning_vector_index = np.searchsorted(cumulative_prob_vector, r)
    transport_choice, next_city = np.unravel_index(winning_vector_index, probability_matrix.shape)

    return transport_choice, next_city


def get_ant_path(city_extra_points, punishment_graph, start_city, target_city, phermone_levels, alpha, beta, time_limit):

    current_city = start_city
    nbr_of_cities = len(city_extra_points)
    temp_city_extra_points = np.copy(city_extra_points)
    travelled_graph = np.zeros(shape=punishment_graph.shape)
    travelled_path = []    # list of tuples (transport_choice, from_node, to_node)

    target_node_reached = False
    i = 0
    total_time = 0
    while not target_node_reached:
        temp_city_extra_points[current_city] = 0  # no additional points for going to the same node again
        transport_choice, next_city = get_next_city(current_city, temp_city_extra_points, phermone_levels, punishment_graph, alpha, beta)
        travelled_graph[transport_choice, current_city, next_city] += 1
        travelled_path.append((transport_choice, current_city, next_city))
        current_city = next_city
        if next_city == target_city:
            target_node_reached = True
        i += 1
        if i > 2*nbr_of_cities:
            raise AntGotLostException()

    return travelled_graph, travelled_path


def evaluate_path_2d(punishment_matrix, city_extra_points, travelled_matrix):
    total_punishment = np.nansum(punishment_matrix * travelled_matrix)
    visited_cities = np.sum(travelled_matrix > 0, axis=1) > 0
    total_city_extra_point = np.sum(city_extra_points[visited_cities])

    #score = total_city_extra_point / total_punishment
    score = 1/total_punishment

    return score    # Maybe return travel time, punishment, score as different values


def evaluate_path(punishment_graph, city_extra_points, travelled_graph):
    total_punishment = np.nansum(punishment_graph * travelled_graph)
    visited_cities = np.sum(travelled_graph > 0, axis=(0, 1)) > 0

    total_city_extra_point = np.sum(city_extra_points[visited_cities])

    #score = total_city_extra_point / total_punishment
    score = 1 / total_punishment

    return score    # Maybe return travel time, punishment, score as different values


def update_pheromones(old_pheromones, all_paths, all_scores, evaporation):

    delta_pheromones = np.zeros(shape=old_pheromones.shape)
    for path, score in zip(all_paths, all_scores):
        delta_pheromones += path * score

    new_pheromones = (1 - evaporation) * old_pheromones + delta_pheromones

    return new_pheromones


def summon_the_ergodic_colony(punishment_graph, city_extra_points, start_city=0, target_city=1, nbr_ants=30,
                              nbr_max_iterations=500, evaporation=0.5, alpha=1.0, beta=3.0,
                              *args, **kwargs):
    import numpy as np
    import time

    pheromones = initiate_pheromones(punishment_graph)

    std_treshold = 0.1    # should be a parameter
    score_std = std_treshold
    i_iteration = 0
    best_path = []
    best_score = 0
    start_time = time.time()
    nbr_lost_ants = 0
    while score_std >= std_treshold and i_iteration <= nbr_max_iterations:
        all_travelled_paths = list()
        all_scores = list()

        for ant in range(nbr_ants):
            try:
                graph, path = get_ant_path(city_extra_points, punishment_graph, start_city, target_city, pheromones, alpha, beta)
                score = evaluate_path(punishment_graph, city_extra_points, graph)

                all_travelled_paths.append(graph)
                all_scores.append(score)

                if score > best_score:
                    best_score = score
                    best_path = path

            except AntGotLostException:
                nbr_lost_ants += 1
                #print('Ant got lost:(')

            if nbr_lost_ants > 0.5*nbr_ants:
                return [], 0

        #print(f'Iteration {i_iteration} of {nbr_max_iterations}', end='')
        i_iteration += 1

        pheromones = update_pheromones(pheromones, all_travelled_paths, all_scores, evaporation)
        score_std = np.std(all_scores/np.mean(all_scores))

    computation_time = time.time() - start_time

    print(f'\nThe Ergodic colony has converged in {i_iteration} of {nbr_max_iterations} iterations!\n'
          f'Best path: {best_path}\n'
          f'Best score: {best_score}\n'
          f'Computation time: {computation_time}\n')

    return best_path, best_score


def run_parallel_colonies(nbr_parallel_jobs, nbr_colonies, *args, **kwargs):
    from joblib import Parallel, delayed

    all_result = Parallel(n_jobs=nbr_parallel_jobs)(delayed(summon_the_ergodic_colony)(args, kwargs)
                                                    for i in range(nbr_colonies))

    best_score = 0
    for res in all_result:
        path = res[0]
        score = res[1]

        if score > best_score:
            best_score = score
            best_path = path

    print(f'Finished! {nbr_parallell_colonies} colonies has converged.\n'
          f'Best score: {best_score}\nBest path: {best_path}')

    return best_path, best_score, all_result