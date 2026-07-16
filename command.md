predict.py \
    --game megamillions \
    --method hot

predict.py \
    --game powerball \
    --method montecarlo

predict.py \
    --game powerball \
    --method randomforest

predict.py \
    --game megamillions \
    --method xgboost

python predict.py --game megamillions --method hot
python predict.py --game powerball --method hot
