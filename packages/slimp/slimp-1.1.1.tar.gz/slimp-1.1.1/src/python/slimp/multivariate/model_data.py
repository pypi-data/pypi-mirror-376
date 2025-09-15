import formulaic
import numpy
import pandas

from .predictor_mapper import PredictorMapper
from . import NoCorrelation

class ModelData:
    def __init__(self, formula, data):
        self.formula = formula
        self.data = data
        
        self.outcomes, self.predictors = zip(
            *[formulaic.model_matrix(f, data) for f in formula])
        self.outcomes = pandas.concat(self.outcomes, axis="columns")
        
        self.predictor_mapper = PredictorMapper(self.predictors, self.outcomes)
        
        mu_y = numpy.mean(self.outcomes.values, axis=0)
        sigma_y = numpy.atleast_1d(numpy.std(self.outcomes.values, axis=0))
        sigma_X = [
            numpy.std(x.filter(regex="^(?!.*Intercept)").values, axis=0)
            for x in self.predictors]
        
        self.fit_data = {
            "R": len(self.formula),
            "N": len(data),
            "K": numpy.squeeze([x.shape[1] for x in self.predictors]),
            "y": numpy.squeeze(self.outcomes.values),
            "X": pandas.concat(self.predictors, axis="columns"),
            
            "mu_alpha": numpy.squeeze(mu_y),
            "sigma_alpha": 2.5*numpy.squeeze(sigma_y),
            "sigma_beta": numpy.hstack(
                [2.5*(sy/sx) for sx, sy in zip(sigma_X, sigma_y)]),
            "lambda_sigma": numpy.squeeze(1/sigma_y),
            "eta_L": 1.0,
            "use_covariance": not isinstance(formula, NoCorrelation)}
    
    def new_predictors(self, data):
        data = data.astype({
            k: v for k, v in self.data.dtypes.items() if k in data.columns})
        predictors = []
        for formula in self.formula:
            predictors.append(
                formulaic.model_matrix(formula.split("~")[1], data))
        predictors = pandas.concat(predictors, axis="columns")
        return predictors
        
    
    def new_data(self, X_new=None):
        if X_new is None:
            X_new = self.fit_data["X"]
        
        return self.fit_data | { "N_new": X_new.shape[0], "X_new": X_new}
