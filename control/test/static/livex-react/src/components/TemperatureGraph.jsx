import React from 'react';
import { useState, useEffect } from 'react';
import Col from 'react-bootstrap/Col';

import { Container, Stack } from 'react-bootstrap';
import { OdinGraph, TitleCard } from 'odin-react';

function TemperatureGraph(props) {
    const {liveXEndPoint} = props;
    // liveXEndPoint = "2";

    const [tempData, changeTempData] = useState([{}]);

    const tempDataA = liveXEndPoint.data.temperature_graph?.thermocouple_a;
    const tempDataB = liveXEndPoint.data.temperature_graph?.thermocouple_b;

    useEffect(() => {
      changeTempData([tempDataA, tempDataB]);
    }, [liveXEndPoint.data.temperature_graph?.thermocouple_a, liveXEndPoint.data.temperature_graph?.thermocouple_b])

    return (
        <Container>
          <Col>
            <TitleCard title="temperature graph">
                <OdinGraph prop_data={tempData} series_names={["TC1", "TC2"]}>
                </OdinGraph>
            </TitleCard>
          </Col>
        </Container>
    )
}

export default TemperatureGraph;