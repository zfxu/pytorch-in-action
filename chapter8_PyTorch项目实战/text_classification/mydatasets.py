import os
import re
import tarfile
import urllib

from torchtext import data


class TarDataset(data.Dataset):
    """Defines a Dataset loaded from a downloadable tar archive.

    Attributes:
        url: URL where the tar archive can be downloaded.
        filename: Filename of the downloaded tar archive.
        dirname: Name of the top-level directory within the zip archive that
            contains the data files.
    """

    @classmethod
    def download_or_unzip(cls, root):
        path = os.path.join(root, cls.dirname)
        if not os.path.isdir(path):
            tpath = os.path.join(root, cls.filename)
            if not os.path.isfile(tpath):
                print('downloading')
                urllib.request.urlretrieve(cls.url, tpath)
            with tarfile.open(tpath, 'r') as tfile:
                print('extracting')
                tfile.extractall(root)
        return os.path.join(path, '')


class NEWS_20(TarDataset):
    url = 'http://people.csail.mit.edu/jrennie/20Newsgroups/20news-bydate.tar.gz'
    filename = 'data/20news-bydate-train'
    dirname = ''

    @staticmethod
    def sort_key(ex):
        return len(ex.text)

    def __init__(self, text_field, label_field, path=None, text_cnt=1000, examples=None, **kwargs):
        """Create an MR dataset instance given a path and fields.

        Arguments:
            text_field: The field that will be used for text data.

            label_field: The field that will be used for label data.
            path: Path to the data file.
            examples: The examples contain all the data.
            Remaining keyword arguments: Passed to the constructor of
                data.Dataset.
        """

        def clean_str(string):
            """
            Tokenization/string cleaning for all datasets except for SST.
            Original taken from https://github.com/yoonkim/CNN_sentence/blob/master/process_data.py
            """
            string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
            string = re.sub(r"\'s", " \'s", string)
            string = re.sub(r"\'ve", " \'ve", string)
            string = re.sub(r"n\'t", " n\'t", string)
            string = re.sub(r"\'re", " \'re", string)
            string = re.sub(r"\'d", " \'d", string)
            string = re.sub(r"\'ll", " \'ll", string)
            string = re.sub(r",", " , ", string)
            string = re.sub(r"!", " ! ", string)
            string = re.sub(r"\(", " \( ", string)
            string = re.sub(r"\)", " \) ", string)
            string = re.sub(r"\?", " \? ", string)
            string = re.sub(r"\s{2,}", " ", string)
            return string.strip().lower()

        text_field.preprocessing = data.Pipeline(clean_str)
        fields = [('text', text_field), ('label', label_field)]

        categories = ['alt.atheism', 'comp.graphics', 'sci.med', 'soc.religion.christian']
        if examples is None:
            path = self.dirname if path is None else path
            examples = []
            for sub_path in categories:

                sub_path_one = os.path.join(path, sub_path)
                sub_paths_two = os.listdir(sub_path_one)
                cnt = 0
                for sub_path_two in sub_paths_two:
                    lines = ""
                    with open(os.path.join(sub_path_one, sub_path_two), encoding="utf8", errors='ignore') as f:
                        lines = f.read()
                    examples += [data.Example.fromlist([lines, sub_path], fields)]
                    cnt += 1

        super(NEWS_20, self).__init__(examples, fields, **kwargs)

    @classmethod
    def splits(cls, text_field, label_field, root='./data',
               train='20news-bydate-train', test='20news-bydate-test',
               **kwargs):
        """Create dataset objects for splits of the 20news dataset.

        Arguments:
            text_field: The field that will be used for the sentence.
            label_field: The field that will be used for label data.

            train: The filename of the train data. Default: 'train.txt'.
            Remaining keyword arguments: Passed to the splits method of
                Dataset.
        """

        path = cls.download_or_unzip(root)

        train_data = None if train is None else cls(
            text_field, label_field, os.path.join(path, train), 2000, **kwargs)

        dev_ratio = 0.1
        dev_index = -1 * int(dev_ratio * len(train_data))

        return (cls(text_field, label_field, examples=train_data[:dev_index]),
                cls(text_field, label_field, examples=train_data[dev_index:]))
