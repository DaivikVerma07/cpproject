from flask import Flask, jsonify, render_template, request
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    subjects = [col for col in numeric_cols if col.lower() not in ['id', 'rollno', 's.no', 'roll number']]
    
    df['Total'] = df[subjects].sum(axis=1)
    
    if 'Name' not in df.columns:
        if 'RollNo' in df.columns:
            df['Name'] = 'Roll No ' + df['RollNo'].astype(str)
        else:
            df['Name'] = ['Student ' + str(i+1) for i in range(len(df))]

    # 1. Subject Stats
    subject_stats = {}
    for sub in subjects:
        subject_stats[sub] = {
            'Average': round(float(df[sub].mean()), 2),
            'Highest': int(df[sub].max()),
            'Lowest': int(df[sub].min())
        }

    # 2. Grade Distribution 
    distribution = {'Needs Work (0-40)': 0, 'Average (41-70)': 0, 'Excellent (71-100)': 0}
    for sub in subjects:
        distribution['Needs Work (0-40)'] += int(len(df[df[sub] <= 40]))
        distribution['Average (41-70)'] += int(len(df[(df[sub] > 40) & (df[sub] <= 70)]))
        distribution['Excellent (71-100)'] += int(len(df[df[sub] > 70]))

    # 3. Leaderboard
    top_3_df = df.nlargest(3, 'Total')
    top_3 = top_3_df[['Name', 'Total']].to_dict('records')
    
    # 4. Data for Radar Chart (FIXED NUMPY SERIALIZATION HERE)
    class_averages = [subject_stats[sub]['Average'] for sub in subjects]
    top_student_scores = [int(x) for x in top_3_df.iloc[0][subjects].tolist()] if not top_3_df.empty else []

    # 5. Full Student List
    df = df.fillna(0)
    all_students = df[['Name', 'Total'] + subjects].to_dict('records')

    return jsonify({
        'subjects': subjects,
        'subject_stats': subject_stats,
        'distribution': distribution,
        'leaderboard': top_3,
        'class_averages': class_averages,
        'top_student_scores': top_student_scores,
        'top_student_name': top_3[0]['Name'] if top_3 else "Top Student",
        'all_students': all_students
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)