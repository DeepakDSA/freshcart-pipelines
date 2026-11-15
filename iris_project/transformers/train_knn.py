from sklearn.neighbors import KNeighborsClassifier

# Import Mage's decorators only if they aren't already loaded
if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

FEATURES = ['sepal length (cm)', 'sepal width (cm)',
            'petal length (cm)', 'petal width (cm)']


# A second model, running as a parallel branch next to train_model.
# It gets the same 150-row table (with the 'split' column) from prepare_data,
# so both models are trained and tested on exactly the same rows.
@transformer
def train_knn(df, *args, **kwargs):
    k = int(kwargs.get('n_neighbors', 5))

    train_df = df[df['split'] == 'train']
    test_df = df[df['split'] == 'test'].copy()

    model = KNeighborsClassifier(n_neighbors=k)
    model.fit(train_df[FEATURES], train_df['target'])

    test_df['predicted'] = model.predict(test_df[FEATURES])
    accuracy = (test_df['predicted'] == test_df['target']).mean()
    print(f'KNN n_neighbors = {k} | Test accuracy = {round(accuracy, 3)}')
    return test_df


# Same quality gate as the decision tree: a KNN below 80% accuracy fails the block.
@test
def test_knn_accuracy(output, *args):
    assert len(output) == 30, 'KNN should predict exactly the 30 test rows'
    accuracy = (output['predicted'] == output['target']).mean()
    assert accuracy >= 0.8, 'KNN accuracy is below 80%'
