package br.gov.educacao.sp.pecobservation.adapters.recording

import android.content.Context
import android.media.MediaRecorder
import android.os.Build
import br.gov.educacao.sp.pecobservation.domain.entities.AudioRecordingResult
import br.gov.educacao.sp.pecobservation.domain.errors.RecordingError
import br.gov.educacao.sp.pecobservation.ports.AudioRecordingPort
import br.gov.educacao.sp.pecobservation.ports.RecordingState
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import java.io.File
import java.security.MessageDigest
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MediaRecorderAdapter @Inject constructor(
    @ApplicationContext private val context: Context,
) : AudioRecordingPort {

    private val _state = MutableStateFlow(RecordingState.IDLE)
    override val state: StateFlow<RecordingState> = _state.asStateFlow()

    private val _elapsedSeconds = MutableStateFlow(0)
    override val elapsedSeconds: StateFlow<Int> = _elapsedSeconds.asStateFlow()

    private var recorder: MediaRecorder? = null
    private var outputFile: File? = null
    private var timerJob: kotlinx.coroutines.Job? = null
    private var currentObservationId: UUID? = null

    override suspend fun requestPermission(): Boolean {
        // Permission must be requested from the UI layer before calling this.
        // Here we check if the app already has the permission granted.
        val pm = context.packageManager
        val result = pm.checkPermission(
            android.Manifest.permission.RECORD_AUDIO,
            context.packageName,
        )
        return result == android.content.pm.PackageManager.PERMISSION_GRANTED
    }

    override suspend fun startRecording(observationId: UUID) {
        if (_state.value == RecordingState.RECORDING)
            throw RecordingError.AlreadyRecording()

        _state.value = RecordingState.PREPARING
        currentObservationId = observationId

        val recordingsDir = File(context.filesDir, "recordings").also { it.mkdirs() }
        val file = File(recordingsDir, "$observationId.m4a")
        outputFile = file

        val rec = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(context)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }

        rec.apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            setAudioSamplingRate(44_100)
            setAudioChannels(1)
            setAudioEncodingBitRate(128_000)
            setOutputFile(file.absolutePath)
            prepare()
            start()
        }

        recorder = rec
        _elapsedSeconds.value = 0
        _state.value = RecordingState.RECORDING
        startTimer()
    }

    override suspend fun pauseRecording() {
        if (_state.value != RecordingState.RECORDING)
            throw RecordingError.NotRecording()
        recorder?.pause()
        timerJob?.cancel()
        _state.value = RecordingState.PAUSED
    }

    override suspend fun resumeRecording() {
        if (_state.value != RecordingState.PAUSED)
            throw RecordingError.NotRecording()
        recorder?.resume()
        startTimer()
        _state.value = RecordingState.RECORDING
    }

    override suspend fun stopRecording(): AudioRecordingResult {
        if (_state.value != RecordingState.RECORDING && _state.value != RecordingState.PAUSED)
            throw RecordingError.NotRecording()

        _state.value = RecordingState.STOPPING
        timerJob?.cancel()

        withContext(Dispatchers.IO) {
            recorder?.apply { stop(); release() }
            recorder = null
        }

        val file = outputFile ?: error("No output file")
        val duration = _elapsedSeconds.value
        val checksum = withContext(Dispatchers.IO) { sha256(file) }

        _state.value = RecordingState.COMPLETED

        return AudioRecordingResult(
            observationId   = currentObservationId!!,
            localFilePath   = file.absolutePath,
            durationSeconds = duration,
            fileSizeBytes   = file.length(),
            checksum        = checksum,
        )
    }

    override fun cancelRecording() {
        timerJob?.cancel()
        recorder?.apply { runCatching { stop() }; release() }
        recorder = null
        outputFile?.delete()
        outputFile = null
        _state.value = RecordingState.IDLE
        _elapsedSeconds.value = 0
    }

    private fun startTimer() {
        timerJob = kotlinx.coroutines.GlobalScope.launch(Dispatchers.Default) {
            while (true) {
                kotlinx.coroutines.delay(1_000)
                _elapsedSeconds.value++
            }
        }
    }

    private fun sha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { stream ->
            val buffer = ByteArray(8_192)
            var read: Int
            while (stream.read(buffer).also { read = it } != -1)
                digest.update(buffer, 0, read)
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }
}
