SELECT id_misuratore, name, eventhub_connection_string, eventhub_consumer_group
FROM hydro.tab_misuratori
WHERE eventhub_connection_string IS NOT NULL AND eventhub_connection_string <> ''
AND eventhub_consumer_group IS NOT NULL AND eventhub_consumer_group <> '';
