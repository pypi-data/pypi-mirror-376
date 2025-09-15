
import jpype
from line_solver import jlineMatrixToArray, jlineMatrixFromArray


def cache_mva(gamma, m):
    ret = jpype.JPackage('jline').api.cache.Cache_mvaKt.cache_mva(
        jlineMatrixFromArray(gamma),
        jlineMatrixFromArray(m)
    )

    pi = jlineMatrixToArray(ret.pi)
    pi0 = jlineMatrixToArray(ret.pi0)
    pij = jlineMatrixToArray(ret.pij)
    x = jlineMatrixToArray(ret.x)
    u = jlineMatrixToArray(ret.u)
    E = jlineMatrixToArray(ret.E)

    return pi, pi0, pij, x, u, E


def cache_prob_asy(gamma, m):
    result = jpype.JPackage('jline').api.cache.Cache_prob_asyKt.cache_prob_asy(
        jlineMatrixFromArray(gamma),
        jlineMatrixFromArray(m)
    )

    return jlineMatrixToArray(result)


def cache_gamma_lp(lambda_array, R):
    java_lambda = jpype.JArray(jpype.JPackage('jline').util.matrix.Matrix)(len(lambda_array))
    for i, matrix in enumerate(lambda_array):
        java_lambda[i] = jlineMatrixFromArray(matrix)

    java_R = jpype.JArray(jpype.JArray(jpype.JPackage('jline').util.matrix.Matrix))(len(R))
    for i, R_row in enumerate(R):
        java_R[i] = jpype.JArray(jpype.JPackage('jline').util.matrix.Matrix)(len(R_row))
        for j, matrix in enumerate(R_row):
            java_R[i][j] = jlineMatrixFromArray(matrix)

    result = jpype.JPackage('jline').api.cache.Cache_gamma_lpKt.cache_gamma_lp(
        java_lambda, java_R
    )

    return jlineMatrixToArray(result.gamma), result.u, result.n, result.h


def cache_rayint(gamma, m):
    result = jpype.JPackage('jline').api.cache.Cache_rayintKt.cache_rayint(
        jlineMatrixFromArray(gamma),
        jlineMatrixFromArray(m)
    )

    return result.Z, result.lZ, jlineMatrixToArray(result.xi)


def cache_xi_fp(gamma, m, xi=None):
    xi_matrix = jlineMatrixFromArray(xi) if xi is not None else None

    result = jpype.JPackage('jline').api.cache.Cache_xi_fpKt.cache_xi_fp(
        jlineMatrixFromArray(gamma),
        jlineMatrixFromArray(m),
        xi_matrix
    )

    return (jlineMatrixToArray(result.xi),
            jlineMatrixToArray(result.pi0),
            jlineMatrixToArray(result.pij),
            result.it)


def cache_miss_rayint(gamma, m, lambda_cell):
    if hasattr(lambda_cell, 'get') and hasattr(lambda_cell, 'length'):
        java_lambda = lambda_cell
    else:
        java_lambda = jpype.JPackage('jline').util.matrix.MatrixCell(len(lambda_cell))
        for i, matrix in enumerate(lambda_cell):
            java_lambda.add(jlineMatrixFromArray(matrix))

    result = jpype.JPackage('jline').api.cache.Cache_miss_rayintKt.cache_miss_rayint(
        jlineMatrixFromArray(gamma),
        jlineMatrixFromArray(m),
        java_lambda
    )

    return (result.M,
            list(result.MU),
            list(result.MI),
            list(result.pi0),
            result.lE)


def cache_prob_erec(gamma, m):
    return jlineMatrixToArray(
        jpype.JPackage('jline').api.cache.Cache_prob_erecKt.cache_prob_erec(
            jlineMatrixFromArray(gamma),
            jlineMatrixFromArray(m)
        )
    )


def cache_prob_fpi(gamma, m):
    return jlineMatrixToArray(
        jpype.JPackage('jline').api.cache.Cache_prob_fpiKt.cache_prob_fpi(
            jlineMatrixFromArray(gamma),
            jlineMatrixFromArray(m)
        )
    )


def cache_prob_rayint(gamma, m):
    return jlineMatrixToArray(
        jpype.JPackage('jline').api.cache.Cache_prob_rayintKt.cache_prob_rayint(
            jlineMatrixFromArray(gamma),
            jlineMatrixFromArray(m)
        )
    )

def cache_erec(parameters):
    if isinstance(parameters, dict):
        result = jpype.JPackage('jline').api.cache.Cache_erecKt.cache_erec(parameters)
    else:
        result = jpype.JPackage('jline').api.cache.Cache_erecKt.cache_erec(
            jlineMatrixFromArray(parameters)
        )

    return result if isinstance(result, (int, float)) else jlineMatrixToArray(result)


def cache_t_hlru(lambda_rates, capacities, n_levels=2):
    return jpype.JPackage('jline').api.cache.Cache_t_hlruKt.cache_t_hlru(
        jlineMatrixFromArray(lambda_rates),
        jlineMatrixFromArray(capacities),
        jpype.JInt(n_levels)
    )


def cache_t_lrum(lambda_rates, capacity, m_parameter=1):
    return jpype.JPackage('jline').api.cache.Cache_t_lrumKt.cache_t_lrum(
        jlineMatrixFromArray(lambda_rates),
        jpype.JInt(capacity),
        jpype.JInt(m_parameter)
    )


def cache_t_lrum_map(MAP, capacity, m_parameter=1):
    if isinstance(MAP, tuple):
        D0, D1 = MAP
        return jpype.JPackage('jline').api.cache.Cache_t_lrum_mapKt.cache_t_lrum_map(
            jlineMatrixFromArray(D0),
            jlineMatrixFromArray(D1),
            jpype.JInt(capacity),
            jpype.JInt(m_parameter)
        )
    else:
        return jpype.JPackage('jline').api.cache.Cache_t_lrum_mapKt.cache_t_lrum_map(
            MAP,
            jpype.JInt(capacity),
            jpype.JInt(m_parameter)
        )


def cache_ttl_hlru(lambda_rates, capacities, ttl_values):
    return jlineMatrixToArray(
        jpype.JPackage('jline').api.cache.Cache_ttl_hlruKt.cache_ttl_hlru(
            jlineMatrixFromArray(lambda_rates),
            jlineMatrixFromArray(capacities),
            jlineMatrixFromArray(ttl_values)
        )
    )


def cache_ttl_lrua(lambda_rates, capacity, alpha=1.0):
    return jlineMatrixToArray(
        jpype.JPackage('jline').api.cache.Cache_ttl_lruaKt.cache_ttl_lrua(
            jlineMatrixFromArray(lambda_rates),
            jpype.JInt(capacity),
            jpype.JDouble(alpha)
        )
    )


def cache_ttl_lrum(lambda_rates, capacity, m_parameter=1):
    return jlineMatrixToArray(
        jpype.JPackage('jline').api.cache.Cache_ttl_lrumKt.cache_ttl_lrum(
            jlineMatrixFromArray(lambda_rates),
            jpype.JInt(capacity),
            jpype.JInt(m_parameter)
        )
    )


def cache_ttl_lrum_map(MAP, capacity, m_parameter=1):
    if isinstance(MAP, tuple):
        D0, D1 = MAP
        return jlineMatrixToArray(
            jpype.JPackage('jline').api.cache.Cache_ttl_lrum_mapKt.cache_ttl_lrum_map(
                jlineMatrixFromArray(D0),
                jlineMatrixFromArray(D1),
                jpype.JInt(capacity),
                jpype.JInt(m_parameter)
            )
        )
    else:
        return jlineMatrixToArray(
            jpype.JPackage('jline').api.cache.Cache_ttl_lrum_mapKt.cache_ttl_lrum_map(
                MAP,
                jpype.JInt(capacity),
                jpype.JInt(m_parameter)
            )
        )


def cache_ttl_tree(lambda_rates, tree_structure, capacities):
    return jlineMatrixToArray(
        jpype.JPackage('jline').api.cache.Cache_ttl_treeKt.cache_ttl_tree(
            jlineMatrixFromArray(lambda_rates),
            jlineMatrixFromArray(tree_structure),
            jlineMatrixFromArray(capacities)
        )
    )


def cache_xi_bvh(lambda_rates, capacity, bvh_params):
    if isinstance(bvh_params, dict):
        return jpype.JPackage('jline').api.cache.Cache_xi_bvhKt.cache_xi_bvh(
            jlineMatrixFromArray(lambda_rates),
            jpype.JInt(capacity),
            bvh_params
        )
    else:
        return jpype.JPackage('jline').api.cache.Cache_xi_bvhKt.cache_xi_bvh(
            jlineMatrixFromArray(lambda_rates),
            jpype.JInt(capacity),
            jlineMatrixFromArray(bvh_params)
        )


def cache_miss(gamma, m, lambda_matrix=None):
    gamma_matrix = jlineMatrixFromArray(gamma)
    m_vector = jlineMatrixFromArray(m)

    if lambda_matrix is not None:
        lambda_mat = jlineMatrixFromArray(lambda_matrix)
        result = jpype.JPackage('jline').api.cache.Cache_missKt.cache_miss(
            gamma_matrix, m_vector, lambda_mat
        )

        return {
            'global_miss_rate': result.getGlobalMissRate(),
            'per_user_miss_rate': jlineMatrixToArray(result.getPerUserMissRate()) if result.getPerUserMissRate() else None,
            'per_item_miss_rate': jlineMatrixToArray(result.getPerItemMissRate()) if result.getPerItemMissRate() else None,
            'per_item_miss_prob': jlineMatrixToArray(result.getPerItemMissProb()) if result.getPerItemMissProb() else None
        }
    else:
        result = jpype.JPackage('jline').api.cache.Cache_missKt.cache_miss(
            gamma_matrix, m_vector, None
        )

        return {
            'global_miss_rate': result.getGlobalMissRate(),
            'per_user_miss_rate': None,
            'per_item_miss_rate': None,
            'per_item_miss_prob': None
        }


def cache_mva_miss(p, m, R):
    result = jpype.JPackage('jline').api.cache.Cache_mva_missKt.cache_mva_miss(
        jlineMatrixFromArray(p),
        jlineMatrixFromArray(m),
        jlineMatrixFromArray(R)
    )

    overall_miss_rate = result.getFirst()
    per_item_miss_prob = jlineMatrixToArray(result.getSecond())

    return overall_miss_rate, per_item_miss_prob


def cache_miss_asy(gamma, m, max_iter=1000, tolerance=1e-8):
    return jpype.JPackage('jline').api.cache.Cache_miss_asyKt.cache_miss_asy(
        jlineMatrixFromArray(gamma),
        jlineMatrixFromArray(m),
        jpype.JInt(max_iter),
        jpype.JDouble(tolerance)
    )


def cache_erec_aux(gamma, m, k):
    return jlineMatrixToArray(
        jpype.JPackage('jline').api.cache.Cache_erecKt.cache_erec_aux(
            jlineMatrixFromArray(gamma),
            jlineMatrixFromArray(m),
            jpype.JInt(k)
        )
    )


def cache_miss_rayint(gamma, m, lambda_matrix):
    from line_solver.lang import MatrixCell
    if not isinstance(lambda_matrix, MatrixCell):
        lambda_cell = MatrixCell.from_array(lambda_matrix)
    else:
        lambda_cell = lambda_matrix

    java_result = jpype.JPackage('jline').api.cache.Cache_miss_rayintKt.cache_miss_rayint(
        jlineMatrixFromArray(gamma),
        jlineMatrixFromArray(m),
        lambda_cell._java_object
    )

    result = {
        'miss_rate': float(java_result.getMissRate()) if hasattr(java_result, 'getMissRate') else None,
        'user_miss_rates': jlineMatrixToArray(java_result.getUserMissRates()) if hasattr(java_result, 'getUserMissRates') else None,
        'item_miss_rates': jlineMatrixToArray(java_result.getItemMissRates()) if hasattr(java_result, 'getItemMissRates') else None,
        'item_miss_probs': jlineMatrixToArray(java_result.getItemMissProbs()) if hasattr(java_result, 'getItemMissProbs') else None
    }
    return result


def cache_par(R, j):
    java_result = jpype.JPackage('jline').api.cache.Cache_gamma_lpKt.cache_par(
        jlineMatrixFromArray(R),
        jpype.JInt(j)
    )

    return [int(item) for item in java_result]


def cache_t_hlru_aux(x, gamma, m, n, h):
    return jlineMatrixToArray(
        jpype.JPackage('jline').api.cache.Cache_t_hlruKt.cache_t_hlru_aux(
            jpype.JArray(jpype.JDouble)(list(x)),
            jlineMatrixFromArray(gamma),
            jlineMatrixFromArray(m),
            jpype.JInt(n),
            jpype.JInt(h)
        )
    )


def cache_t_lrum_aux(x, gamma, m, n, h):
    return jlineMatrixToArray(
        jpype.JPackage('jline').api.cache.Cache_t_lrumKt.cache_t_lrum_aux(
            jpype.JArray(jpype.JDouble)(list(x)),
            jlineMatrixFromArray(gamma),
            jlineMatrixFromArray(m),
            jpype.JInt(n),
            jpype.JInt(h)
        )
    )




def cache_gamma_approx(gamma, m, options=None):
    import numpy as np
    from scipy.cluster.vq import kmeans2
    from scipy.linalg import svd
    from sklearn.decomposition import PCA

    gamma = np.array(gamma)
    C, I = gamma.shape

    if options is None:
        options = {}

    method = options.get('method', 'svd')
    preserve_rowsum = options.get('preserve_rowsum', True)

    original_rowsums = np.sum(gamma, axis=1) if preserve_rowsum else None

    approximation_info = {
        'method': method,
        'original_shape': gamma.shape,
        'original_nnz': np.count_nonzero(gamma),
        'original_frobenius_norm': np.linalg.norm(gamma, 'fro')
    }

    if method == 'svd':
        target_rank = options.get('rank', min(C, I) // 2)
        target_rank = min(target_rank, min(C, I))

        U, s, Vt = svd(gamma)

        s_approx = s.copy()
        s_approx[target_rank:] = 0

        gamma_approx = U @ np.diag(s_approx) @ Vt

        approximation_info.update({
            'rank': target_rank,
            'singular_values_kept': target_rank,
            'energy_preserved': np.sum(s[:target_rank]**2) / np.sum(s**2)
        })

    elif method == 'kmeans':
        n_clusters = options.get('clusters', max(1, I // 10))
        n_clusters = min(n_clusters, I)

        _, labels = kmeans2(gamma.T, n_clusters)

        gamma_approx = np.zeros((C, n_clusters))
        for k in range(n_clusters):
            cluster_mask = (labels == k)
            if np.sum(cluster_mask) > 0:
                gamma_approx[:, k] = np.sum(gamma[:, cluster_mask], axis=1)

        approximation_info.update({
            'clusters': n_clusters,
            'compression_ratio': I / n_clusters
        })

    elif method == 'sparse':
        threshold = options.get('threshold', 1e-6)

        gamma_approx = gamma.copy()
        gamma_approx[np.abs(gamma_approx) < threshold] = 0

        approximation_info.update({
            'threshold': threshold,
            'sparsity_ratio': 1 - np.count_nonzero(gamma_approx) / gamma.size
        })

    elif method == 'pca':
        n_components = options.get('rank', min(C, I) // 2)
        n_components = min(n_components, min(C, I))

        pca = PCA(n_components=n_components)
        gamma_transformed = pca.fit_transform(gamma.T)
        gamma_approx = pca.inverse_transform(gamma_transformed).T

        approximation_info.update({
            'components': n_components,
            'explained_variance_ratio': np.sum(pca.explained_variance_ratio_)
        })

    elif method == 'quantize':
        n_levels = options.get('levels', 16)

        gamma_min, gamma_max = np.min(gamma), np.max(gamma)
        levels = np.linspace(gamma_min, gamma_max, n_levels)

        gamma_approx = np.zeros_like(gamma)
        for i in range(gamma.shape[0]):
            for j in range(gamma.shape[1]):
                closest_idx = np.argmin(np.abs(levels - gamma[i, j]))
                gamma_approx[i, j] = levels[closest_idx]

        approximation_info.update({
            'quantization_levels': n_levels,
            'dynamic_range': gamma_max - gamma_min
        })

    else:
        raise ValueError(f"Unknown approximation method: {method}")

    if preserve_rowsum and original_rowsums is not None:
        current_rowsums = np.sum(gamma_approx, axis=1)
        for i in range(C):
            if current_rowsums[i] > 0:
                gamma_approx[i, :] *= original_rowsums[i] / current_rowsums[i]

    error = np.linalg.norm(gamma - gamma_approx, 'fro')
    relative_error = error / np.linalg.norm(gamma, 'fro') if np.linalg.norm(gamma, 'fro') > 0 else 0

    approximation_info.update({
        'approximated_shape': gamma_approx.shape,
        'approximated_nnz': np.count_nonzero(gamma_approx),
        'error': float(error),
        'relative_error': float(relative_error),
        'compression_achieved': gamma.size / gamma_approx.size if hasattr(gamma_approx, 'size') else 1.0
    })

    return {
        'gamma_approx': gamma_approx,
        'approximation_info': approximation_info
    }


def cache_opt_capacity(gamma, constraints=None, options=None):
    import numpy as np
    from scipy.optimize import minimize, differential_evolution

    gamma = np.array(gamma)
    C, I = gamma.shape

    if constraints is None:
        constraints = {}

    if options is None:
        options = {}

    total_capacity = constraints.get('total_capacity', C * 50)
    per_cache_max = constraints.get('per_cache_max', total_capacity)
    per_cache_min = constraints.get('per_cache_min', 1)
    cost_per_unit = constraints.get('cost_per_unit', np.ones(C))
    max_cost = constraints.get('max_cost', np.inf)

    objective = options.get('objective', 'miss_rate')
    algorithm = options.get('algorithm', 'gradient')
    max_iterations = options.get('max_iterations', 1000)
    tolerance = options.get('tolerance', 1e-6)

    cost_per_unit = np.array(cost_per_unit)
    if cost_per_unit.size == 1:
        cost_per_unit = np.full(C, cost_per_unit[0])

    def objective_function(capacities):
        """Compute objective function value for given capacities."""
        capacities = np.maximum(capacities, per_cache_min)
        capacities = np.minimum(capacities, per_cache_max)

        if objective == 'miss_rate':
            total_requests = np.sum(gamma, axis=1)
            hit_rates = np.minimum(capacities / (total_requests + 1e-10), 1.0)
            miss_rates = 1.0 - hit_rates
            return np.mean(miss_rates)

        elif objective == 'throughput':
            total_requests = np.sum(gamma, axis=1)
            hit_rates = np.minimum(capacities / (total_requests + 1e-10), 1.0)
            throughputs = hit_rates * total_requests
            return -np.sum(throughputs)

        elif objective == 'cost_efficiency':
            total_requests = np.sum(gamma, axis=1)
            hit_rates = np.minimum(capacities / (total_requests + 1e-10), 1.0)
            throughputs = hit_rates * total_requests
            total_cost = np.sum(cost_per_unit * capacities)
            efficiency = np.sum(throughputs) / (total_cost + 1e-10)
            return -efficiency

        else:
            raise ValueError(f"Unknown objective: {objective}")

    def constraint_function(capacities):
        """Compute constraint violations."""
        violations = []

        if np.sum(capacities) > total_capacity:
            violations.append(np.sum(capacities) - total_capacity)

        for i in range(C):
            if capacities[i] > per_cache_max:
                violations.append(capacities[i] - per_cache_max)
            if capacities[i] < per_cache_min:
                violations.append(per_cache_min - capacities[i])

        total_cost = np.sum(cost_per_unit * capacities)
        if total_cost > max_cost:
            violations.append(total_cost - max_cost)

        return sum(violations)

    bounds = [(per_cache_min, min(per_cache_max, total_capacity)) for _ in range(C)]

    x0 = np.full(C, total_capacity / C)
    x0 = np.maximum(x0, per_cache_min)
    x0 = np.minimum(x0, per_cache_max)

    optimization_info = {
        'algorithm': algorithm,
        'objective': objective,
        'max_iterations': max_iterations,
        'tolerance': tolerance
    }

    if algorithm == 'gradient':
        constraints_scipy = [
            {'type': 'ineq', 'fun': lambda x: total_capacity - np.sum(x)},
            {'type': 'ineq', 'fun': lambda x: max_cost - np.sum(cost_per_unit * x)}
        ]

        result = minimize(
            objective_function,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_scipy,
            options={'maxiter': max_iterations, 'ftol': tolerance}
        )

        optimal_capacities = result.x
        optimal_value = result.fun
        optimization_info.update({
            'success': result.success,
            'iterations': result.nit,
            'message': result.message
        })

    elif algorithm == 'genetic':
        population_size = options.get('population_size', 50)

        def objective_with_penalty(capacities):
            obj_val = objective_function(capacities)
            penalty = 1000 * max(0, constraint_function(capacities))
            return obj_val + penalty

        result = differential_evolution(
            objective_with_penalty,
            bounds,
            seed=42,
            popsize=population_size,
            maxiter=max_iterations,
            tol=tolerance
        )

        optimal_capacities = result.x
        optimal_value = objective_function(optimal_capacities)
        optimization_info.update({
            'success': result.success,
            'iterations': result.nit,
            'message': result.message
        })

    elif algorithm == 'grid':
        grid_points = options.get('grid_points', 10)

        capacity_ranges = [np.linspace(b[0], b[1], grid_points) for b in bounds]

        best_obj = np.inf
        best_capacities = None

        import itertools

        total_combinations = grid_points ** C
        if total_combinations > 10000:
            n_samples = 10000
            combinations = []
            for _ in range(n_samples):
                combo = [np.random.choice(range_vals) for range_vals in capacity_ranges]
                combinations.append(combo)
        else:
            combinations = itertools.product(*capacity_ranges)

        evaluated = 0
        for combo in combinations:
            capacities = np.array(combo)

            if (np.sum(capacities) <= total_capacity and
                np.sum(cost_per_unit * capacities) <= max_cost):

                obj_val = objective_function(capacities)
                if obj_val < best_obj:
                    best_obj = obj_val
                    best_capacities = capacities

            evaluated += 1

        optimal_capacities = best_capacities if best_capacities is not None else x0
        optimal_value = best_obj if best_obj < np.inf else objective_function(x0)

        optimization_info.update({
            'success': best_capacities is not None,
            'evaluations': evaluated,
            'grid_points': grid_points
        })

    else:
        raise ValueError(f"Unknown optimization algorithm: {algorithm}")

    sensitivity_analysis = {}
    if optimal_capacities is not None:
        perturbation = 0.01
        sensitivities = np.zeros(C)

        for i in range(C):
            perturbed_caps = optimal_capacities.copy()
            perturbed_caps[i] *= (1 + perturbation)

            if (np.sum(perturbed_caps) <= total_capacity and
                np.sum(cost_per_unit * perturbed_caps) <= max_cost):
                obj_perturbed = objective_function(perturbed_caps)
                sensitivities[i] = (obj_perturbed - optimal_value) / (perturbation * optimal_capacities[i])

        sensitivity_analysis = {
            'capacity_sensitivity': sensitivities,
            'most_sensitive_cache': int(np.argmax(np.abs(sensitivities))),
            'least_sensitive_cache': int(np.argmin(np.abs(sensitivities)))
        }

    return {
        'optimal_capacities': optimal_capacities,
        'optimal_value': optimal_value,
        'optimization_info': optimization_info,
        'sensitivity_analysis': sensitivity_analysis
    }

