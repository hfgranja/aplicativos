#if os(iOS)
import SwiftUI

public struct SyncStatusView: View {
    @Environment(AppDependencies.self) private var deps
    @State private var viewModel: SyncStatusViewModel?

    public init() {}

    public var body: some View {
        NavigationStack {
            if let vm = viewModel {
                List {
                    Section("Status") {
                        LabeledContent("Pendentes", value: "\(vm.pendingCount)")
                        if let last = vm.lastSyncAt {
                            LabeledContent("Última sincronização",
                                           value: last.formatted(date: .abbreviated, time: .shortened))
                        }
                        if let error = vm.syncError {
                            Text(error).foregroundStyle(.red).font(.caption)
                        }
                    }

                    Section {
                        Button(action: { Task { await vm.syncNow() } }) {
                            HStack {
                                if vm.isSyncing {
                                    ProgressView().padding(.trailing, 8)
                                }
                                Text(vm.isSyncing ? "Sincronizando..." : "Sincronizar agora")
                            }
                        }
                        .disabled(vm.isSyncing)
                    }
                }
                .navigationTitle("Sincronização")
                .onAppear { vm.refreshStatus() }
                .refreshable { await vm.syncNow() }
            } else {
                ProgressView()
                    .onAppear {
                        viewModel = SyncStatusViewModel(
                            syncQueue: deps.syncQueue,
                            syncUseCase: deps.syncUseCase
                        )
                    }
            }
        }
    }
}
#endif
