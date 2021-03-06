# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Contains a collection of util functions for model construction.
"""
import numpy
import tensorflow as tf
from tensorflow import logging
from tensorflow import flags
import tensorflow.contrib.slim as slim

def SampleRandomSequence(model_input, num_frames, num_samples):
  """Samples a random sequence of frames of size num_samples.

  Args:
    model_input: A tensor of size batch_size x max_frames x feature_size
    num_frames: A tensor of size batch_size x 1
    num_samples: A scalar

  Returns:
    `model_input`: A tensor of size batch_size x num_samples x feature_size
  """

  batch_size = tf.shape(model_input)[0]
  frame_index_offset = tf.tile(
      tf.expand_dims(tf.range(num_samples), 0), [batch_size, 1])
  max_start_frame_index = tf.maximum(num_frames - num_samples, 0)
  start_frame_index = tf.cast(
      tf.multiply(
          tf.random_uniform([batch_size, 1]),
          tf.cast(max_start_frame_index + 1, tf.float32)), tf.int32)
  frame_index = tf.minimum(start_frame_index + frame_index_offset,
                           tf.cast(num_frames - 1, tf.int32))
  batch_index = tf.tile(
      tf.expand_dims(tf.range(batch_size), 1), [1, num_samples])
  index = tf.stack([batch_index, frame_index], 2)
  return tf.gather_nd(model_input, index)


def SampleRandomFrames(model_input, num_frames, num_samples):
  """Samples a random set of frames of size num_samples.

  Args:
    model_input: A tensor of size batch_size x max_frames x feature_size
    num_frames: A tensor of size batch_size x 1
    num_samples: A scalar

  Returns:
    `model_input`: A tensor of size batch_size x num_samples x feature_size
  """
  batch_size = tf.shape(model_input)[0]
  frame_index = tf.cast(
      tf.multiply(
          tf.random_uniform([batch_size, num_samples]),
          tf.tile(tf.cast(num_frames, tf.float32), [1, num_samples])), tf.int32)
  batch_index = tf.tile(
      tf.expand_dims(tf.range(batch_size), 1), [1, num_samples])
  index = tf.stack([batch_index, frame_index], 2)
  return tf.gather_nd(model_input, index)


def SampleASequence(model_input, num_frames, num_samples):
  batch_size = tf.shape(model_input)[0]
  interv = tf.tile(tf.cast(num_frames, tf.float32), [1, num_samples]) / num_samples
  frame_index = tf.cast(
      tf.multiply((tf.tile(tf.expand_dims(tf.cast(tf.range(num_samples), tf.float32), 0), [batch_size, 1]) + tf.random_uniform([batch_size, num_samples])), interv), tf.int32)
  batch_index = tf.tile(
      tf.expand_dims(tf.range(batch_size), 1), [1, num_samples])
  index = tf.stack([batch_index, tf.minimum(frame_index, tf.tile(tf.cast(num_frames, tf.int32), [1, num_samples]))], 2)
  return tf.gather_nd(model_input, index)
  
def MeanASequence(model_input, num_frames, num_samples):
  batch_size = tf.shape(model_input)[0]
  interv = tf.cast(tf.cast(num_frames, tf.float32) / num_samples, tf.int32)
  
  model_inputs = tf.unstack(model_input)
  intervs = tf.unstack(interv)
  num_framess = tf.unstack(num_frames)
  output = []
  print model_input.get_shape().as_list()
  for i in range(model_input.get_shape().as_list()[0]):
    start_frame_index = tf.cast(
      tf.multiply(
          tf.random_uniform([1]),
          tf.cast(num_framess[i] - intervs[i]*num_samples, tf.float32)), tf.int32)
    tmp = model_inputs[i][start_frame_index[0]:start_frame_index[0]+intervs[i]*num_samples, :]
    tmp = tf.reshape(tmp, [num_samples, intervs[i], 1024])
    output.append(tf.reduce_mean(tmp, 1))
  return tf.stack(output, 0)
  
def MaxASequence(model_input, num_frames, num_samples):
  batch_size = tf.shape(model_input)[0]
  interv = tf.cast(tf.cast(num_frames, tf.float32) / num_samples, tf.int32)
  
  model_inputs = tf.unstack(model_input)
  intervs = tf.unstack(interv)
  num_framess = tf.unstack(num_frames)
  output = []
  print model_input.get_shape().as_list()
  for i in range(model_input.get_shape().as_list()[0]):
    start_frame_index = tf.cast(
      tf.multiply(
          tf.random_uniform([1]),
          tf.cast(num_framess[i] - intervs[i]*num_samples, tf.float32)), tf.int32)
    tmp = model_inputs[i][start_frame_index[0]:start_frame_index[0]+intervs[i]*num_samples, :]
    tmp = tf.reshape(tmp, [num_samples, intervs[i], 1024])
    output.append(tf.reduce_max(tmp, 1))
  return tf.stack(output, 0)
    
  
def FramePooling(frames, method, **unused_params):
  """Pools over the frames of a video.

  Args:
    frames: A tensor with shape [batch_size, num_frames, feature_size].
    method: "average", "max", "attention", or "none".
  Returns:
    A tensor with shape [batch_size, feature_size] for average, max, or
    attention pooling. A tensor with shape [batch_size*num_frames, feature_size]
    for none pooling.

  Raises:
    ValueError: if method is other than "average", "max", "attention", or
    "none".
  """
  if method == "average":
    return tf.reduce_mean(frames, 1)
  elif method == "max":
    return tf.reduce_max(frames, 1)
  elif method == "none":
    feature_size = frames.shape_as_list()[2]
    return tf.reshape(frames, [-1, feature_size])
  else:
    raise ValueError("Unrecognized pooling method: %s" % method)
