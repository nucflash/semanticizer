# Copyright 2012-2013, University of Amsterdam. This program is free software:
# you can redistribute it and/or modify it under the terms of the GNU Lesser 
# General Public License as published by the Free Software Foundation, either 
# version 3 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or 
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License 
# for more details.
# 
# You should have received a copy of the GNU Lesser General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from core import LinksProcessor
from util import ModelStore

import warnings

class LearningProcessor(LinksProcessor):
    def __init__(self, model_dir):
        self.modelStore = ModelStore(model_dir)

    def predict(self, classifier, testfeatures):
        print("Start predicting of %d instances with %d features."
              % (len(testfeatures), len(testfeatures[0])))
        predict = classifier.predict_proba(testfeatures)
        print("Done predicting of %d instances." % len(predict))

        return predict    

    def check_model(self, model, description, features, settings):
        if "language" in description:
            assert settings["langcode"] == description["language"], \
                "Language of model and data do not match."
        
        if "features" in description:
            missing_features = set(description["features"]) - set(features)
            if(len(missing_features)):
                warn = RuntimeWarning("Missing %d features for model %s: %s "
                                      % (len(missing_features), 
                                         description["name"],
                                         ", ".join(missing_features)))
                
                if "missing" in settings:
                    warnings.warn(warn)
                else:
                    raise warn

            features = sorted(description["features"])
        
        if model.n_features_ != len(features):
            raise ValueError("Number of features of the model must "
                             "match the input. Model n_features is %s and "
                             "input n_features is %s."
                             % (model.n_features_, len(features)))

        return features

    def process(self, links, text, settings):
        if not "learning" in settings or len(links) == 0:
            return (links, text, settings)
        
        modelname = settings["learning"]
        (model, description) = self.modelStore.load_model(modelname)
        print("Loaded classifier from %s" % description["source"])

        features = sorted(links[0]["features"].keys())        
        features = self.check_model(model, description, features, settings)

        testfeatures = []
        for link in links:
            linkfeatures = []
            for feature in features:
                if feature in link["features"]:
                    linkfeatures.append(link["features"][feature])
                else:
                    linkfeatures.append(None)
            testfeatures.append(linkfeatures)

        scores = self.predict(model, testfeatures)
        for link, score in zip(links, scores):
            link["learning_probability"] = score[1]
            if "features" not in settings:
                del link["features"]

        return (links, text, settings)
