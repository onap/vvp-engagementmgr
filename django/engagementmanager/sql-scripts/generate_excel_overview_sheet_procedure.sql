--
-- ============LICENSE_START==========================================
-- org.onap.vvp/engagementmgr
-- ===================================================================
-- Copyright C 2017 AT&T Intellectual Property. All rights reserved.
-- ===================================================================
--
-- Unless otherwise specified, all software contained herein is licensed
-- under the Apache License, Version 2.0 (the "License");
-- you may not use this software except in compliance with the License.
-- You may obtain a copy of the License at
--
--             http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
--
--
--
-- Unless otherwise specified, all documentation contained herein is licensed
-- under the Creative Commons License, Attribution 4.0 Intl. (the "License");
-- you may not use this documentation except in compliance with the License.
-- You may obtain a copy of the License at
--
--             https://creativecommons.org/licenses/by/4.0/
--
-- Unless required by applicable law or agreed to in writing, documentation
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
--
-- ============LICENSE_END============================================
--
-- ECOMP is a trademark and service mark of AT&T Intellectual Property.
CREATE OR REPLACE FUNCTION generate_excel_overview_sheet(stage TEXT, keyword TEXT)
RETURNS TABLE (name VARCHAR(200),
               active_engagements INTEGER,
               active_vfc_sum INTEGER,
               intake_engagements INTEGER,
               intake_vfc_sum INTEGER,
               completed_engagements INTEGER,
               completed_vfc_sum INTEGER,
               total_engagements INTEGER,
               total_vfc_sum INTEGER) AS $res$
BEGIN
    -- temp tables declarations:
    CREATE TEMP TABLE result
    (
        name VARCHAR(200),
        active_engagements INTEGER,
        active_vfc_sum INTEGER,
        intake_engagements INTEGER,
        intake_vfc_sum INTEGER,
        completed_engagements INTEGER,
        completed_vfc_sum INTEGER,
        total_engagements INTEGER,
        total_vfc_sum INTEGER
    ) ON COMMIT DROP;

    CREATE TEMP TABLE filters
    (
        name VARCHAR(200),
        value VARCHAR(200)
    ) ON COMMIT DROP;

    CREATE TEMP TABLE deployment_targets
    (
        deployment_target_uuid VARCHAR(200),
        deployment_targets INTEGER
    ) ON COMMIT DROP;

    CREATE TEMP TABLE engagement_stages
    (
        engagement_stage VARCHAR(200),
        total INTEGER
    ) ON COMMIT DROP;

    CREATE TEMP TABLE virtual_functions_componenets
    (
        name VARCHAR(200),
        engagement_stage VARCHAR(200)
    ) ON COMMIT DROP;

    CREATE TEMP TABLE ecomp_releases
    (
        ecomp_release_uuid VARCHAR(200),
        ecomp_release_name VARCHAR(200)
    ) ON COMMIT DROP;

    -- Handling filters
    IF $1 = 'All' OR $1 = 'all' OR $1 IS NULL THEN stage := ''; ELSE stage := $1; END IF;
    INSERT INTO filters VALUES('stage', stage);
    IF $2 IS NULL THEN keyword := ''; ELSE keyword := $2; END IF;
    INSERT INTO filters VALUES('keyword', keyword);

    -- handling AIC (deployment targets) rows:
    INSERT INTO deployment_targets
        SELECT deployment_target_id, COUNT(deployment_target_id) AS total FROM ice_vf GROUP BY deployment_target_id;

    -- Itearting throght each deployment:
    DO $$
    DECLARE
       deployment record;
       vf record;
       ecomp record;
       stage TEXT;
       keyword TEXT;
    BEGIN
    	-- Get the filters from outside:
    	SELECT value FROM filters WHERE name = 'stage' LIMIT 1 INTO stage;
        SELECT value FROM filters WHERE name = 'keyword' LIMIT 1 INTO keyword;
        FOR deployment IN SELECT * FROM deployment_targets LOOP
            INSERT INTO engagement_stages
                SELECT ice_engagement.engagement_stage, COUNT(ice_engagement.engagement_stage)
                FROM ice_vf LEFT JOIN ice_engagement ON engagement_id = ice_engagement.uuid
                WHERE ice_vf.deployment_target_id = deployment.deployment_target_uuid
                		AND ice_engagement.engagement_stage LIKE '%' || stage || '%' -- stage param filtering
                    AND (ice_engagement.engagement_manual_id LIKE '%' || keyword || '%' OR ice_vf.name LIKE '%' || keyword || '%') -- keyword param filtering
                    AND ice_engagement.engagement_stage IN ('Active', 'Intake', 'Completed')
                GROUP BY ice_engagement.engagement_stage;

            INSERT INTO virtual_functions_componenets
                SELECT ice_vfc.name, ice_engagement.engagement_stage
                FROM ice_vfc LEFT JOIN ice_vf ON ice_vfc.vf_id = ice_vf.uuid
                             LEFT JOIN ice_engagement ON ice_vf.engagement_id = ice_engagement.uuid
                WHERE ice_vf.deployment_target_id = deployment.deployment_target_uuid
                		AND ice_engagement.engagement_stage LIKE '%' || stage || '%' -- stage param filtering
                    AND (ice_engagement.engagement_manual_id LIKE '%' || keyword || '%' OR ice_vf.name LIKE '%' || keyword || '%' OR ice_vfc.name LIKE '%' || keyword || '%') -- keyword param filtering
                    AND ice_engagement.engagement_stage IN ('Active', 'Intake', 'Completed');

            --Insert the AIC row with its statistics:
            INSERT INTO result VALUES
            ((SELECT version FROM ice_deployment_target WHERE uuid =  deployment.deployment_target_uuid LIMIT 1),
            (SELECT total FROM engagement_stages where engagement_stage = 'Active' LIMIT 1),
             (SELECT COUNT(*) FROM virtual_functions_componenets WHERE engagement_stage = 'Active'),
             (SELECT total FROM engagement_stages where engagement_stage = 'Intake' LIMIT 1),
             (SELECT COUNT(*) FROM virtual_functions_componenets WHERE engagement_stage = 'Intake'),
             (SELECT total FROM engagement_stages where engagement_stage = 'Completed' LIMIT 1),
             (SELECT COUNT(*) FROM virtual_functions_componenets WHERE engagement_stage = 'Completed'),
             (SELECT SUM(total) FROM engagement_stages),
             (SELECT COUNT(*) FROM virtual_functions_componenets)
            );

            --******************************************************************************************************
            --Handling the ecomp release rows:
            INSERT INTO ecomp_releases
                SELECT DISTINCT ice_ecomp_release.uuid, ice_ecomp_release.name
                FROM ice_vf LEFT JOIN ice_ecomp_release ON ice_ecomp_release.uuid = ice_vf.ecomp_release_id
                WHERE ice_vf.deployment_target_id = deployment.deployment_target_uuid;

            FOR ecomp IN SELECT * FROM ecomp_releases LOOP
                --empty the temp tables:
                DELETE FROM virtual_functions_componenets;
                DELETE FROM engagement_stages;

                INSERT INTO engagement_stages
                    SELECT ice_engagement.engagement_stage, COUNT(ice_engagement.engagement_stage)
                    FROM ice_vf LEFT JOIN ice_engagement ON engagement_id = ice_engagement.uuid
                    WHERE ice_vf.deployment_target_id = deployment.deployment_target_uuid AND ice_vf.ecomp_release_id = ecomp.ecomp_release_uuid
                    	AND ice_engagement.engagement_stage LIKE '%' || stage || '%'--stage param filtering
                      AND (ice_engagement.engagement_manual_id LIKE '%' || keyword || '%' OR ice_vf.name LIKE '%' || keyword || '%') --keyword param filtering
                      AND ice_engagement.engagement_stage IN ('Active', 'Intake', 'Completed')
                    GROUP BY ice_engagement.engagement_stage;

                INSERT INTO virtual_functions_componenets
                    SELECT ice_vfc.name, ice_engagement.engagement_stage
                    FROM ice_vfc LEFT JOIN ice_vf ON ice_vfc.vf_id = ice_vf.uuid
                                 LEFT JOIN ice_engagement ON ice_vf.engagement_id = ice_engagement.uuid
                    WHERE ice_vf.deployment_target_id = deployment.deployment_target_uuid AND ice_vf.ecomp_release_id = ecomp.ecomp_release_uuid
                    	AND ice_engagement.engagement_stage LIKE '%' || stage || '%'--stage param filtering
                      AND (ice_engagement.engagement_manual_id LIKE '%' || keyword || '%' OR ice_vf.name LIKE '%' || keyword || '%' OR ice_vfc.name LIKE '%' || keyword || '%') -- keyword param filtering
						          AND ice_engagement.engagement_stage IN ('Active', 'Intake', 'Completed');

                --Insert the ecomp release row with its statistics:
                INSERT INTO result VALUES
                ('	>>' || ecomp.ecomp_release_name,
                (SELECT total FROM engagement_stages where engagement_stage = 'Active' LIMIT 1),
                 (SELECT COUNT(*) FROM virtual_functions_componenets WHERE engagement_stage = 'Active'),
                 (SELECT total FROM engagement_stages where engagement_stage = 'Intake' LIMIT 1),
                 (SELECT COUNT(*) FROM virtual_functions_componenets WHERE engagement_stage = 'Intake'),
                 (SELECT total FROM engagement_stages where engagement_stage = 'Completed' LIMIT 1),
                 (SELECT COUNT(*) FROM virtual_functions_componenets WHERE engagement_stage = 'Completed'),
                 (SELECT SUM(total) FROM engagement_stages),
                 (SELECT COUNT(*) FROM virtual_functions_componenets)
                );
            END LOOP;
            --******************************************************************************************************

            --empty the temp tables:
            DELETE FROM virtual_functions_componenets;
            DELETE FROM engagement_stages;
            DELETE FROM ecomp_releases;
     END LOOP;
    END $$;

    RETURN QUERY SELECT * FROM result;
END;
$res$
LANGUAGE 'plpgsql' VOLATILE;
