/**
 * 简化版 Recorder.js - 基于 Web Audio API 的录音库
 * 支持 WAV 格式录制和导出
 */

(function(window) {
  
  var Recorder = function(source, cfg) {
    var config = cfg || {};
    var bufferLen = config.bufferLen || 4096;
    var numChannels = config.numChannels || 1;
    
    this.context = source.context;
    this.node = (this.context.createScriptProcessor ||
                 this.context.createJavaScriptNode).call(this.context, bufferLen, numChannels, numChannels);
    
    var recording = false;
    var recBuffers = [];
    var recLength = 0;
    
    this.node.onaudioprocess = function(e) {
      if (!recording) return;
      
      var buffer = e.inputBuffer.getChannelData(0);
      recBuffers.push(new Float32Array(buffer));
      recLength += buffer.length;
    };

    this.record = function() {
      recording = true;
      recBuffers = [];
      recLength = 0;
    };

    this.stop = function() {
      recording = false;
    };

    this.clear = function() {
      recBuffers = [];
      recLength = 0;
    };

    this.exportWAV = function(cb, mimeType) {
      var type = mimeType || 'audio/wav';
      var result = new Float32Array(recLength);
      var offset = 0;
      
      for (var i = 0; i < recBuffers.length; i++) {
        result.set(recBuffers[i], offset);
        offset += recBuffers[i].length;
      }
      
      var dataview = encodeWAV(result, numChannels, this.context.sampleRate);
      var audioBlob = new Blob([dataview], { type: type });
      cb(audioBlob);
    };

    source.connect(this.node);
    this.node.connect(this.context.destination);
  };

  function encodeWAV(samples, numChannels, sampleRate) {
    var buffer = new ArrayBuffer(44 + samples.length * 2);
    var view = new DataView(buffer);

    /* RIFF identifier */
    writeString(view, 0, 'RIFF');
    /* RIFF chunk length */
    view.setUint32(4, 36 + samples.length * 2, true);
    /* RIFF type */
    writeString(view, 8, 'WAVE');
    /* format chunk identifier */
    writeString(view, 12, 'fmt ');
    /* format chunk length */
    view.setUint32(16, 16, true);
    /* sample format (raw) */
    view.setUint16(20, 1, true);
    /* channel count */
    view.setUint16(22, numChannels, true);
    /* sample rate */
    view.setUint32(24, sampleRate, true);
    /* byte rate (sample rate * block align) */
    view.setUint32(28, sampleRate * 4, true);
    /* block align (channel count * bytes per sample) */
    view.setUint16(32, numChannels * 2, true);
    /* bits per sample */
    view.setUint16(34, 16, true);
    /* data chunk identifier */
    writeString(view, 36, 'data');
    /* data chunk length */
    view.setUint32(40, samples.length * 2, true);

    floatTo16BitPCM(view, 44, samples);

    return view;
  }

  function floatTo16BitPCM(output, offset, input) {
    for (var i = 0; i < input.length; i++, offset += 2) {
      var s = Math.max(-1, Math.min(1, input[i]));
      output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
  }

  function writeString(view, offset, string) {
    for (var i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  window.Recorder = Recorder;

})(window);