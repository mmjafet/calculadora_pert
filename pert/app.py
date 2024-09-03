from flask import Flask, render_template, request, jsonify
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

def calculate_pert(activities):
    for activity in activities:
        o = activity['optimistic']
        m = activity['most_probable']
        p = activity['pessimistic']
        activity['expected'] = (o + 4 * m + p) / 6

    G = nx.DiGraph()
    for activity in activities:
        if not activity['name']:
            continue  # Skip activities without a name

        predecessors = activity['predecessor'].split(',') if activity['predecessor'] else []
        for predecessor in predecessors:
            if predecessor:
                G.add_edge(predecessor.strip(), activity['name'], weight=activity['expected'])
        if not predecessors:
            G.add_node(activity['name'])

    critical_path = nx.dag_longest_path(G, weight='weight')
    duration = sum(G[u][v]['weight'] for u, v in zip(critical_path[:-1], critical_path[1:]))
    
    # Calculate optimal time
    optimal_time = sum(activity['optimistic'] for activity in activities)
    
    return G, critical_path, duration, optimal_time

def draw_graph(G, critical_path):
    pos = nx.spring_layout(G)
    plt.figure()
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=2000, font_size=10, font_weight='bold')
    nx.draw_networkx_edge_labels(G, pos, edge_labels={(u, v): f"{G[u][v]['weight']:.2f}" for u, v in G.edges})

    critical_edges = [(u, v) for u, v in zip(critical_path[:-1], critical_path[1:])]
    nx.draw_networkx_edges(G, pos, edgelist=critical_edges, edge_color='r', width=2)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()

    return img_base64

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        activities = data['activities']
        
        # Check for empty names and remove them
        activities = [activity for activity in activities if activity['name']]

        G, critical_path, duration, optimal_time = calculate_pert(activities)
        graph_img = draw_graph(G, critical_path)
        
        response = {
            'graph_img': graph_img,
            'critical_path': critical_path,
            'duration': duration,
            'optimal_time': optimal_time,
            'activities': activities  # Include activities with 'expected' calculated
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
