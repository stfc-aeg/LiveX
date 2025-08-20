import '../../App.css';

import '../../index.css'
import 'bootstrap/dist/css/bootstrap.min.css';

import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

import React from "react";
import { useAdapterEndpoint } from 'odin-react';

import KdcController from './KdcController';
import EncoderStage from './EncoderStage';

import KimController from './KimController.jsx';
import PiezoStage from './PiezoStage';

function Motor(props)
{
    const {endpoint_url} = props;

    const kinesisEndPoint = useAdapterEndpoint('kinesis', endpoint_url, 500);
    const controllers = kinesisEndPoint?.data?.controllers;
  
    const componentMap = {
      'kim101': KimController,
      'kdc101': KdcController
    };

    return (
        <Container className='mt-2'>
        {!controllers ? (
        <Row> No controllers found</Row>
        ) : (
        Object.entries(controllers).map(([controllerName, controllerData]) => {
            const ControllerComponent = componentMap[controllerData.type.toLowerCase()];
            if (ControllerComponent) {
            return (
                <ControllerComponent
                key={controllerName}
                name={controllerName}
                motors={controllerData.motors}
                kinesisEndPoint={kinesisEndPoint}
                />
            )
            }
            else {
            return (
                <Row>Unknown controller type: {controllerData.type}</Row>
            )
            }
        }
        ))}
        </Container>
    );
}

export default Motor;
