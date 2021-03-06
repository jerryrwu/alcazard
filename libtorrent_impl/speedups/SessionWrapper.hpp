#ifndef SESSIONWRAPPER_HPP_
#define SESSIONWRAPPER_HPP_

#include <string>
#include <unordered_map>
#include <unordered_set>

#include <sqlite3.h>
#include <libtorrent/alert_types.hpp>
#include <libtorrent/session.hpp>
#include <libtorrent/settings_pack.hpp>
#include <libtorrent/add_torrent_params.hpp>

#include "TorrentState.hpp"
#include "Utils.hpp"

namespace lt = libtorrent;

class SessionWrapper {
private:
    libtorrent::session *session;
    sqlite3 *db;
    bool enable_file_preallocation;
    TimerAccumulator timers;
    int num_initial_torrents;
    int num_loaded_initial_torrents;
    int64_t start_total_downloaded;
    int64_t start_total_uploaded;
    std::shared_ptr <Timer> timer_initial_torrents_received;
    std::vector <std::pair<std::string, int>> metrics_names;
    std::unordered_map <std::string, int64_t> added_torrent_row_ids;
    std::unordered_set <std::string> info_hashes_resume_data_wait;
    std::unordered_map <std::string, TrackerTorrentState> pre_load_tracker_states;
    std::unordered_set <int64_t> loaded_torrent_ids;
    bool succeeded_listening = false;

    void init_settings_pack(lt::settings_pack *pack);
    void read_session_stats();
    void init_metrics_names();
    void init_add_params(lt::add_torrent_params &params, std::string torrent, std::string download_path,
                         std::string *name, std::string *resume_data);
    std::shared_ptr <TorrentState> handle_torrent_added(lt::torrent_status *status);
    void calculate_torrent_count_metrics(BatchTorrentUpdate *update);
    void update_session_stats(BatchTorrentUpdate *update);
    void apply_pre_load_tracker_state(std::shared_ptr <TorrentState> state);
    void on_alert_add_torrent(BatchTorrentUpdate *update, lt::add_torrent_alert *alert);
    void on_alert_state_update(BatchTorrentUpdate *update, lt::state_update_alert *alert);
    void on_alert_session_stats(BatchTorrentUpdate *update, lt::session_stats_alert *alert);
    void on_alert_torrent_finished(BatchTorrentUpdate *update, lt::torrent_finished_alert *alert);
    void on_alert_save_resume_data(BatchTorrentUpdate *update, lt::save_resume_data_alert *alert);
    void on_alert_save_resume_data_failed(BatchTorrentUpdate *update, lt::save_resume_data_failed_alert *alert);
    void on_alert_tracker_announce(BatchTorrentUpdate *update, lt::tracker_announce_alert *alert);
    void on_alert_tracker_reply(BatchTorrentUpdate *update, lt::tracker_reply_alert *alert);
    void on_alert_tracker_error(BatchTorrentUpdate *update, lt::tracker_error_alert *alert);
    void on_alert_torrent_removed(BatchTorrentUpdate *update, lt::torrent_removed_alert *alert);
    void on_alert_listen_succeeded(BatchTorrentUpdate *update, lt::listen_succeeded_alert *alert);
    void on_alert_listen_failed(BatchTorrentUpdate *update, lt::listen_failed_alert *alert);
    void on_alert_storage_moved(BatchTorrentUpdate *update, lt::storage_moved_alert *alert);
    void on_alert_file_renamed(BatchTorrentUpdate *update, lt::file_renamed_alert *alert);

    inline void dispatch_alert(BatchTorrentUpdate *update, lt::alert *alert) {
        if (auto a = lt::alert_cast<lt::add_torrent_alert>(alert)) {
            this->on_alert_add_torrent(update, a);
        } else if (auto a = lt::alert_cast<lt::state_update_alert>(alert)) {
            this->on_alert_state_update(update, a);
        } else if (auto a = lt::alert_cast<lt::session_stats_alert>(alert)) {
            this->on_alert_session_stats(update, a);
        } else if (auto a = lt::alert_cast<lt::torrent_finished_alert>(alert)) {
            this->on_alert_torrent_finished(update, a);
        } else if (auto a = lt::alert_cast<lt::save_resume_data_alert>(alert)) {
            update->save_resume_data_alerts.push_back(a);
        } else if (auto a = lt::alert_cast<lt::save_resume_data_failed_alert>(alert)) {
            this->on_alert_save_resume_data_failed(update, a);
        } else if (auto a = lt::alert_cast<lt::tracker_announce_alert>(alert)) {
            this->on_alert_tracker_announce(update, a);
        } else if (auto a = lt::alert_cast<lt::tracker_reply_alert>(alert)) {
            this->on_alert_tracker_reply(update, a);
        } else if (auto a = lt::alert_cast<lt::tracker_error_alert>(alert)) {
            this->on_alert_tracker_error(update, a);
        } else if (auto a = lt::alert_cast<lt::torrent_removed_alert>(alert)) {
            this->on_alert_torrent_removed(update, a);
        } else if (auto a = lt::alert_cast<lt::listen_succeeded_alert>(alert)) {
            this->on_alert_listen_succeeded(update, a);
        } else if (auto a = lt::alert_cast<lt::listen_failed_alert>(alert)) {
            this->on_alert_listen_failed(update, a);
        } else if (auto a = lt::alert_cast<lt::storage_moved_alert>(alert)) {
            this->on_alert_storage_moved(update, a);
        } else if (auto a = lt::alert_cast<lt::file_renamed_alert>(alert)) {
            this->on_alert_file_renamed(update, a);
        }
    }

    inline void dispatch_alert_shutting_down(BatchTorrentUpdate *update, lt::alert *alert) {
        if (auto a = lt::alert_cast<lt::save_resume_data_alert>(alert)) {
            update->save_resume_data_alerts.push_back(a);
        } else if (auto a = lt::alert_cast<lt::save_resume_data_failed_alert>(alert)) {
            this->on_alert_save_resume_data_failed(update, a);
        }
    }

public:
    std::unordered_map <std::string, std::shared_ptr<TorrentState>> torrent_states;

    SessionWrapper(
            std::string db_path,
            std::string listen_interfaces,
            bool enable_dht,
            bool enable_file_preallocation
    );
    ~SessionWrapper();

    int load_initial_torrents();
    std::shared_ptr <TorrentState> add_torrent(
            std::string torrent,
            std::string download_path,
            std::string *name
    );
    void remove_torrent(std::string info_hash);
    void force_recheck(std::string info_hash);
    std::shared_ptr <TorrentState> pause_torrent(std::string info_hash);
    void resume_torrent(std::string info_hash);
    void rename_torrent(std::string info_hash, std::string name);
    void force_reannounce(std::string info_hash);
    void move_data(std::string info_hash, std::string download_path);
    void post_torrent_updates();
    void pause();
    BatchTorrentUpdate process_alerts(bool shutting_down);
    void post_session_stats();
    void all_torrents_save_resume_data(bool flush_cache);
};

#endif
