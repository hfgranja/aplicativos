package br.gov.educacao.sp.pecobservation

import android.app.Application
import androidx.work.Configuration
import br.gov.educacao.sp.pecobservation.adapters.sync.SyncWorker
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject

@HiltAndroidApp
class PECObservationApp : Application(), Configuration.Provider {

    @Inject lateinit var workManagerConfig: Configuration

    override val workManagerConfiguration: Configuration
        get() = workManagerConfig

    override fun onCreate() {
        super.onCreate()
        SyncWorker.schedule(this)
    }
}
